ALLOWED_PARAM_LAT = 'lat'
ALLOWED_PARAM_LON = 'lon'
ALLOWED_PARAM_RADIUS = 'radius'
ALLOWED_PARAMS = [
  ALLOWED_PARAM_LAT,
  ALLOWED_PARAM_LON,
  ALLOWED_PARAM_RADIUS
]

# valid txt should be in the format ex: lat=20394
def parse_valid_settings(settings):
  # only continue with settings strings that are valid
  valid_settings = _filter_valid_settings(settings)

  settings = {}
  # format settings strings into dict
  for setting in valid_settings:
    split_setting = setting.split('=')
    settings[split_setting[0]] = split_setting[1]

  return settings


def _setting_is_valid(txt):
  split_txt = txt.split('=')
  if len(split_txt) != 2:
    return False
  if split_txt[0] not in ALLOWED_PARAMS:
    return False
  if not _is_valid_value(split_txt[0], split_txt[1]):
    return False

  return True


def _filter_valid_settings(settings):
  return list(filter(_setting_is_valid, settings))


def _is_valid_value(key, value):
  if key == ALLOWED_PARAM_LAT or key == ALLOWED_PARAM_LON:
    return _is_txt_float(value)
  elif key == ALLOWED_PARAM_RADIUS:
    return _is_txt_int(value)
  else:
    return False


def _is_txt_float(txt):
  try:
    float(txt)
  except Exception as e:
    return False
  else:
    return True

def _is_txt_int(txt):
  try:
    int(txt)
  except Exception as e:
    return False
  else:
    return True


