from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.mosecom import MOSECOM_DUST_CODES, MOSECOM_GAS_CODES
from app.core.values import to_float
from app.models.cagg_profile_inversion_hourly import CaggProfileInversionHourly
from app.models.device_state import DeviceState
from app.models.dust_state import DustState
from app.models.gas_sensors import GasSensors
from app.models.ivtm_state import IvtmState
from app.models.meteo_state import MeteoState
from app.models.monitoring_posts import MonitoringPost
from app.models.mosecom_hourly_reading import MosecomHourlyReading
from app.models.mosecom_profile_hourly import MosecomProfileHourly
from app.models.plc_state import PlcState
from app.models.pollutant_limit import PollutantLimit
from app.models.profile_level import ProfileLevel
from app.models.profile_state import ProfileState
from app.schemas.station_readings import (
    LatestDustOut,
    LatestGasOut,
    LatestGasSubstanceOut,
    LatestIvtmOut,
    LatestMeteoOut,
    LatestProfileLevelOut,
    LatestProfileOut,
    PollutantLimitOut,
    StationLatestResponse,
)


def get_latest_readings(db: Session, monitoring_post_id: int) -> StationLatestResponse:
    limits_by_code = _pollutant_limits_by_code(db)
    post = db.get(MonitoringPost, monitoring_post_id)
    if post is not None and post.source == "mosecom":
        return _latest_mosecom_readings(db, monitoring_post_id, limits_by_code)

    gas = _latest_raw_gas(db, monitoring_post_id, limits_by_code)
    dust = _latest_raw_dust(db, monitoring_post_id, limits_by_code)
    meteo = _latest_raw_meteo(db, monitoring_post_id)
    ivtm = _latest_raw_ivtm(db, monitoring_post_id)
    profile = _latest_raw_profile(db, monitoring_post_id)
    timestamps = [
        item.timestamp_ms
        for item in (gas, dust, meteo, ivtm, profile)
        if item is not None
    ]

    return StationLatestResponse(
        monitoring_post_id=monitoring_post_id,
        timestamp_ms=max(timestamps, default=None),
        time_mode="exact",
        gas=gas,
        dust=dust,
        meteo=meteo,
        ivtm=ivtm,
        profile=profile,
    )


def _latest_mosecom_readings(
    db: Session,
    monitoring_post_id: int,
    limits_by_code: dict[str, PollutantLimit],
) -> StationLatestResponse:
    gas_timestamp_ms = _latest_mosecom_timestamp(db, monitoring_post_id, MOSECOM_GAS_CODES)
    dust_timestamp_ms = _latest_mosecom_timestamp(db, monitoring_post_id, MOSECOM_DUST_CODES)
    profile = _latest_mosecom_profile(db, monitoring_post_id)
    timestamp_ms = max(
        (
            timestamp
            for timestamp in (
                gas_timestamp_ms,
                dust_timestamp_ms,
                profile.timestamp_ms if profile is not None else None,
            )
            if timestamp is not None
        ),
        default=None,
    )

    gas = None
    if gas_timestamp_ms is not None:
        gas_rows = db.scalars(
            select(MosecomHourlyReading)
            .where(
                MosecomHourlyReading.monitoring_post_id == monitoring_post_id,
                MosecomHourlyReading.bucket_ms == gas_timestamp_ms,
                MosecomHourlyReading.substance_code.in_(MOSECOM_GAS_CODES),
            )
            .order_by(MosecomHourlyReading.substance_code.asc())
        ).all()
        gas = LatestGasOut(
            timestamp_ms=gas_timestamp_ms,
            substances=[
                LatestGasSubstanceOut(
                    substance_code=row.substance_code,
                    value=to_float(row.value_avg),
                    limit=_limit_out(limits_by_code.get(row.substance_code.upper())),
                )
                for row in gas_rows
            ],
        )

    dust = None
    if dust_timestamp_ms is not None:
        dust_rows = {
            row.substance_code: row
            for row in db.scalars(
                select(MosecomHourlyReading).where(
                    MosecomHourlyReading.monitoring_post_id == monitoring_post_id,
                    MosecomHourlyReading.bucket_ms == dust_timestamp_ms,
                    MosecomHourlyReading.substance_code.in_(MOSECOM_DUST_CODES),
                )
            ).all()
        }
        dust = LatestDustOut(
            timestamp_ms=dust_timestamp_ms,
            pm1=None,
            pm2=to_float(dust_rows["PM2.5"].value_avg) if "PM2.5" in dust_rows else None,
            pm10=to_float(dust_rows["PM10"].value_avg) if "PM10" in dust_rows else None,
            tsp=None,
            limits={
                "pm2": _limit_out(limits_by_code.get("PM2.5")),
                "pm10": _limit_out(limits_by_code.get("PM10")),
            },
        )

    return StationLatestResponse(
        monitoring_post_id=monitoring_post_id,
        timestamp_ms=timestamp_ms,
        time_mode="hourly",
        gas=gas,
        dust=dust,
        meteo=None,
        ivtm=None,
        profile=profile,
    )


def _latest_mosecom_timestamp(
    db: Session,
    monitoring_post_id: int,
    substance_codes: tuple[str, ...],
) -> int | None:
    return db.scalar(
        select(MosecomHourlyReading.bucket_ms)
        .where(
            MosecomHourlyReading.monitoring_post_id == monitoring_post_id,
            MosecomHourlyReading.substance_code.in_(substance_codes),
        )
        .order_by(MosecomHourlyReading.bucket_ms.desc())
        .limit(1)
    )


def _latest_measurement_key(
    db: Session,
    model: type,
    monitoring_post_id: int,
    *value_columns: object,
    required_columns: tuple[object, ...] = (),
) -> tuple[int, int] | None:
    conditions = [PlcState.monitoring_post_id == monitoring_post_id]
    if value_columns:
        conditions.append(or_(*(column.is_not(None) for column in value_columns)))
    conditions.extend(column.is_not(None) for column in required_columns)

    row = db.execute(
        select(model.device_state_id, model.device_timestamp_ms)
        .join(DeviceState, DeviceState.id == model.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(*conditions)
        .order_by(model.device_timestamp_ms.desc(), model.device_state_id.desc())
        .limit(1)
    ).first()
    return (int(row.device_state_id), int(row.device_timestamp_ms)) if row else None


def _latest_raw_gas(
    db: Session,
    monitoring_post_id: int,
    limits_by_code: dict[str, PollutantLimit],
) -> LatestGasOut | None:
    key = _latest_measurement_key(
        db,
        GasSensors,
        monitoring_post_id,
        GasSensors.value,
        required_columns=(GasSensors.substance_code,),
    )
    if key is None:
        return None

    device_state_id, timestamp_ms = key
    rows = db.scalars(
        select(GasSensors)
        .where(
            GasSensors.device_state_id == device_state_id,
            GasSensors.device_timestamp_ms == timestamp_ms,
            GasSensors.substance_code.is_not(None),
            GasSensors.value.is_not(None),
        )
        .order_by(GasSensors.sensor_id.asc())
    ).all()
    return LatestGasOut(
        timestamp_ms=timestamp_ms,
        substances=[
            LatestGasSubstanceOut(
                substance_code=row.substance_code,
                value=to_float(row.value),
                limit=_limit_out(limits_by_code.get(row.substance_code.upper())),
            )
            for row in rows
        ],
    )


def _latest_raw_dust(
    db: Session,
    monitoring_post_id: int,
    limits_by_code: dict[str, PollutantLimit],
) -> LatestDustOut | None:
    key = _latest_measurement_key(
        db,
        DustState,
        monitoring_post_id,
        DustState.pm1_concentration,
        DustState.pm2_concentration,
        DustState.pm10_concentration,
        DustState.tsp_concentration,
    )
    if key is None:
        return None

    row = db.get(DustState, key)
    return LatestDustOut(
        timestamp_ms=key[1],
        pm1=to_float(row.pm1_concentration),
        pm2=to_float(row.pm2_concentration),
        pm10=to_float(row.pm10_concentration),
        tsp=to_float(row.tsp_concentration),
        limits={
            "pm1": _limit_out(limits_by_code.get("PM1")),
            "pm2": _limit_out(limits_by_code.get("PM2.5")),
            "pm10": _limit_out(limits_by_code.get("PM10")),
            "tsp": _limit_out(limits_by_code.get("TSP")),
        },
    )


def _latest_raw_meteo(db: Session, monitoring_post_id: int) -> LatestMeteoOut | None:
    key = _latest_measurement_key(
        db,
        MeteoState,
        monitoring_post_id,
        MeteoState.atm_press,
        MeteoState.air_temp,
        MeteoState.air_hum,
        MeteoState.hor_win_dir,
        MeteoState.hor_win_spd,
    )
    if key is None:
        return None

    row = db.get(MeteoState, key)
    return LatestMeteoOut(
        timestamp_ms=key[1],
        atm_press=to_float(row.atm_press),
        air_temp=to_float(row.air_temp),
        air_hum=to_float(row.air_hum),
        hor_win_dir=to_float(row.hor_win_dir),
        hor_win_spd=to_float(row.hor_win_spd),
    )


def _latest_raw_ivtm(db: Session, monitoring_post_id: int) -> LatestIvtmOut | None:
    key = _latest_measurement_key(
        db,
        IvtmState,
        monitoring_post_id,
        IvtmState.sensor_ivtm_hum,
        IvtmState.sensor_ivtm_temp,
    )
    if key is None:
        return None

    row = db.get(IvtmState, key)
    return LatestIvtmOut(
        timestamp_ms=key[1],
        sensor_ivtm_hum=to_float(row.sensor_ivtm_hum),
        sensor_ivtm_temp=to_float(row.sensor_ivtm_temp),
    )


def _latest_raw_profile(db: Session, monitoring_post_id: int) -> LatestProfileOut | None:
    key = _latest_measurement_key(db, ProfileLevel, monitoring_post_id, ProfileLevel.temperature)
    if key is None:
        return None

    device_state_id, timestamp_ms = key
    level_rows = db.scalars(
        select(ProfileLevel)
        .where(
            ProfileLevel.device_state_id == device_state_id,
            ProfileLevel.device_timestamp_ms == timestamp_ms,
            ProfileLevel.temperature.is_not(None),
        )
        .order_by(ProfileLevel.height.asc())
    ).all()
    inversion = db.get(ProfileState, key)
    return LatestProfileOut(
        timestamp_ms=timestamp_ms,
        levels=[
            LatestProfileLevelOut(height=float(row.height), temperature=to_float(row.temperature))
            for row in level_rows
        ],
        inversion_power=to_float(inversion.inversion_power) if inversion else None,
        inversion_lower=to_float(inversion.inversion_lower) if inversion else None,
        inversion_upper=to_float(inversion.inversion_upper) if inversion else None,
        inversion_delta_t=to_float(inversion.inversion_delta_t) if inversion else None,
    )


def _latest_mosecom_profile(db: Session, monitoring_post_id: int) -> LatestProfileOut | None:
    timestamp_ms = db.scalar(
        select(MosecomProfileHourly.bucket_ms)
        .where(MosecomProfileHourly.monitoring_post_id == monitoring_post_id)
        .order_by(MosecomProfileHourly.bucket_ms.desc())
        .limit(1)
    )
    if timestamp_ms is None:
        return None

    rows = db.scalars(
        select(MosecomProfileHourly)
        .where(
            MosecomProfileHourly.monitoring_post_id == monitoring_post_id,
            MosecomProfileHourly.bucket_ms == timestamp_ms,
        )
        .order_by(MosecomProfileHourly.height.asc())
    ).all()
    inversion = db.get(
        CaggProfileInversionHourly,
        (timestamp_ms, monitoring_post_id),
    )
    return LatestProfileOut(
        timestamp_ms=timestamp_ms,
        levels=[
            LatestProfileLevelOut(height=float(row.height), temperature=to_float(row.temperature_avg))
            for row in rows
        ],
        inversion_power=to_float(inversion.inversion_power_avg) if inversion else None,
        inversion_lower=to_float(inversion.inversion_lower_avg) if inversion else None,
        inversion_upper=to_float(inversion.inversion_upper_avg) if inversion else None,
        inversion_delta_t=to_float(inversion.inversion_delta_t_avg) if inversion else None,
    )


def _pollutant_limits_by_code(db: Session) -> dict[str, PollutantLimit]:
    limit_rows = db.execute(select(PollutantLimit)).scalars().all()
    return {row.pollutant_code.upper(): row for row in limit_rows}


def _limit_out(limit: PollutantLimit | None) -> PollutantLimitOut | None:
    if limit is None:
        return None
    return PollutantLimitOut(
        pollutant_code=limit.pollutant_code,
        pdk_max_once=to_float(limit.pdk_max_once),
        pdk_daily=to_float(limit.pdk_daily),
        pdk_annual=to_float(limit.pdk_annual),
        comparison_pdk=to_float(limit.pdk_max_once),
        comparison_kind="max_once",
    )
