MOSECOM_GAS_CODES = ("NO2", "O3", "NO", "SO2", "CO", "H2S")
MOSECOM_DUST_CODE_TO_METRIC = {
    "PM2.5": "pm2_concentration",
    "PM10": "pm10_concentration",
}
MOSECOM_DUST_CODES = tuple(MOSECOM_DUST_CODE_TO_METRIC)
