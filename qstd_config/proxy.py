import copy

exclude_proxy_fields = frozenset(['_state', '_config_dict', 'dict'])


class ProxyConfigDictContener:
    def __init__(self, config_dict):
        self.config_dict = config_dict


class ProxyConfig:
    def __init__(self, config_dict: ProxyConfigDictContener, value=None):
        self._state = value
        self._config_dict = config_dict

    def __getattribute__(self, item):
        if item in exclude_proxy_fields:
            return object.__getattribute__(self, item)
        if self._state is None:
            value = self._config_dict.config_dict.get(item)
        else:
            value = self._state.get(item)
        if isinstance(value, dict):
            return ProxyConfig(self._config_dict, value)
        if isinstance(value, list):
            return [ProxyConfig(self._config_dict, val) if isinstance(val, dict) else val for val in value]
        return value

    def dict(self):
        return copy.deepcopy(self._config_dict.config_dict)
