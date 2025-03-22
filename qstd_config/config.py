import abc
import collections
import typing
import inspect

from pydantic import create_model, BaseModel
# noinspection PyProtectedMember
from pydantic._internal._decorators import PydanticDescriptorProxy

from . import utils


class ConfigProperty:
    key: str
    env: str
    path: typing.List[str]

    def __init__(self, key: str, parts: typing.List[str]):
        self.key = key
        self.env = '_'.join([utils.unify_name(name) for name in parts])
        self.path = parts

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in vars(self).items())})"


class _ConfigMeta(abc.ABCMeta):
    """
    A metaclass that provides functionality for managing nested configuration structures
    and automatically generating Pydantic models for configuration validation.

    This metaclass is responsible for:
    - Identifying nested configuration fields.
    - Generating Pydantic validation models for configuration fields.
    - Ensuring that configuration fields are properly validated and mapped from raw input data.
    """
    def __new__(cls, name: str, bases: tuple, dct: dict):
        """
        Creates a new class that includes additional functionality for managing
        configuration fields and generating Pydantic models for validation.

        This method is called when a class inherits from BaseConfig. It processes
        the fields, adds validation logic, and builds the necessary Pydantic model.

        Args:
            name (str): The name of the class being created.
            bases (tuple): The base classes for the new class.
            dct (dict): The dictionary of class attributes and methods.

        Returns:
            type: The newly created configuration class with additional functionality.
        """
        result_cls = super().__new__(cls, name, bases, dct)

        nested_configuration_cls = []
        configuration_properties = []
        all_properties = []
        pydantic_fields = {}
        pydantic_validators = {}
        for _cls in result_cls.__mro__:
            for _name, value in utils.get_annotations(_cls).items():
                all_properties.append(_name)
                _type = cls._cast_nested_configuration_type_to_pydantic(value)
                if _type is not None:
                    nested_configuration_cls.append(_name)
                else:
                    _type = value
                pydantic_fields[_name] = (_type, cls._get_default_value(_cls, _name))
                configuration_properties.extend(cls._compile_property_list(_name, value))
            for method_name, method in _cls.__dict__.items():
                if isinstance(method, PydanticDescriptorProxy):
                    pydantic_validators[method_name] = method
        pydantic_model = create_model(
            'ConfigValidator',
            **dict(__validators__=pydantic_validators),
            **pydantic_fields
        )
        pydantic_model.__qstd_config_cls__ = result_cls
        result_cls.__qstd_pydantic_cls__ = pydantic_model
        result_cls.__qstd_nested_configuration_fields__ = frozenset(nested_configuration_cls)
        result_cls.__qstd_configuration_properties__ = configuration_properties
        result_cls.__qstd_all_properties__ = frozenset(all_properties)
        return result_cls

    @classmethod
    def _get_default_value(cls, _cls, name: str):
        """
        Retrieves the default value for a given configuration field.

        Args:
            _cls (type): The class that defines the field.
            name (str): The name of the configuration field.

        Returns:
            The default value of the configuration field, or ... if no default is provided.
        """
        if hasattr(_cls, name):
            return getattr(_cls, name)
        else:
            return ...

    @classmethod
    def _is_base_config(cls, value: typing.Any) -> bool:
        """
        Checks if the given value is a subclass of _BaseConfig, indicating that
        it is a nested configuration class.

        Args:
            value (typing.Any): The value to check.

        Returns:
            bool: True if the value is a subclass of _BaseConfig, False otherwise.
        """
        try:
            if inspect.isclass(value):
                return issubclass(value, BaseConfig)
        except TypeError:
            pass
        return False

    @classmethod
    def _is_type(cls, value: typing.Any) -> bool:
        """
        Checks if the given value is a parameterized type (e.g., List[int], Dict[str, str]).

        Args:
            value (typing.Any): The value to check.

        Returns:
            bool: True if the value is a parameterized type, False otherwise.
        """
        return typing.get_origin(value) is not None

    @classmethod
    def _cast_nested_configuration_type_to_pydantic(cls, value: typing.Any) -> typing.Optional[typing.Any]:
        """
        Casts a nested configuration type to its corresponding Pydantic model type
        if the type includes a nested configuration. If the type does not contain
        a nested configuration, returns None.

        Args:
            value (typing.Any): The value (type) to cast.

        Returns:
            typing.Optional[typing.Any]: The corresponding Pydantic model type if
                                         the type contains a nested configuration,
                                         or None if the type does not include a nested configuration.
        """
        if cls._is_base_config(value):
            return value.__qstd_pydantic_cls__
        if not cls._is_type(value):
            return
        _type_origin = typing.get_origin(value)
        _type_args = list(typing.get_args(value))
        has_config_subclass = False
        for index, _type_arg in enumerate(_type_args):
            _type = cls._cast_nested_configuration_type_to_pydantic(_type_arg)
            if _type is not None:
                if _type_origin is set:
                    raise Exception('Nested configuration types cannot be part of a set')
                has_config_subclass = True
                _type_args[index] = _type
        if has_config_subclass:
            return _type_origin[tuple(_type_args)]

    @classmethod
    def _is_single_type_with_configuration(cls, value: typing.Any) -> bool:
        """
         Checks if the value is a type that can be used for single configuration fields (e.g., Annotated, Optional).

         Args:
             value (typing.Any): The value to check.

         Returns:
             bool: True if the value is a single type configuration, False otherwise.
         """
        is_single_type = any(
            typing.get_origin(value) is t for t in (
                typing.Annotated, typing.Optional, typing.Set
            )
        )
        if is_single_type is False:
            return False
        _type_args = typing.get_args(value)
        for _type_arg in _type_args:
            if cls._is_single_type_with_configuration(_type_arg):
                return True
        return False

    @classmethod
    def _compile_property_list(
        cls,
        name: str,
        value,
        current_path: typing.List[str] = None
    ) -> typing.List[ConfigProperty]:
        """
        Compiles the list of configuration properties for the given field, including
        nested configuration fields if applicable.

        Args:
            name (str): The name of the configuration field.
            value (Any): The value (type) of the configuration field.
            current_path (List[str]): The current path of the configuration field.

        Returns:
            List[ConfigProperty]: A list of ConfigProperty objects representing
                                   the configuration properties.
        """
        if current_path is None:
            current_path = []
        properties = []
        next_path = list(current_path)
        next_path.append(name)
        if cls._is_base_config(value):
            for config_property in value.__qstd_configuration_properties__:
                property_path = list(next_path)
                property_path.extend(config_property.path)
                properties.append(ConfigProperty(
                    key=config_property.key, parts=property_path
                ))
        elif cls._is_single_type_with_configuration(value):
            for _type_arg in typing.get_args(value):
                properties.extend(cls._compile_property_list(name, _type_arg, list(next_path)))
        else:
            properties.append(ConfigProperty(
                key=name,
                parts=next_path
            ))
        return properties


class BaseConfig(metaclass=_ConfigMeta):
    """
    The base class for all configuration classes. It provides methods for handling
    configuration properties, including nested configurations and validation.

    This class is intended to be inherited by other configuration classes to define
    the structure and validation rules for the configuration data.
    """
    def __repr__(self):
        return self._repr_str()

    def __str__(self):
        return self._repr_str()

    def _repr_str(self):
        return (
            f"{type(self).__name__}"
            f"({', '.join(f'{k}={v!r}' for k, v in self.__dict__.items() if not k.startswith('_'))})"
        )

    def __update_configuration__(self, valid_data: BaseModel):
        """
         Updates the configuration using new validated data. Nested configuration fields
         are updated recursively. Non-configuration types (e.g., lists, dicts) are replaced
         with new values.

         Args:
             valid_data (BaseModel): A Pydantic validated model instance containing
                                      the updated configuration data.
         """
        raise NotImplementedError


class InMemoryConfig(BaseConfig):
    """
    A configuration class that stores and manages configuration data in memory.
    This class inherits from _BaseConfig and allows for nested configuration
    structures to be validated and mapped from raw input data.
    """

    def __init__(self, valid_data: BaseModel):
        """
        Initializes the InMemoryConfig instance by mapping the provided validated
        data (from Pydantic) to the internal configuration structure, including
        nested configurations and basic fields.

        Args:
            valid_data (BaseModel): A Pydantic validated model instance containing
                                     the configuration data.
        """
        valid_dict = valid_data.model_dump()
        for name in self.__qstd_nested_configuration_fields__:
            if valid_dict[name] is not None:
                valid_dict[name] = self._mapping_child_value(getattr(valid_data, name))
        for attr, value in valid_dict.items():
            setattr(self, attr, value)

    @classmethod
    def _mapping_child_value(cls, value: typing.Any):
        """
         Recursively replaces instances of BaseModel with instances of a configuration class
         inheriting from BaseConfig. It also handles lists, tuples, frozensets, and dicts,
         mapping each element or key to the corresponding configuration model.

         The method identifies all models and replaces them with configuration classes,
         including within nested structures.

         Args:
             value (typing.Any): The value to map, which can be a BaseModel, list, tuple, frozenset, or dict.

         Returns:
             The mapped value, where instances of BaseModel are replaced with configuration class instances,
             and other types (e.g., lists, dicts) are handled appropriately.
         """
        if isinstance(value, BaseModel):
            return value.__qstd_config_cls__(value)
        elif isinstance(value, list):
            return [cls._mapping_child_value(item) for item in value]
        elif isinstance(value, tuple):
            return tuple(cls._mapping_child_value(item) for item in value)
        elif isinstance(value, frozenset):
            return collections.deque(cls._mapping_child_value(item) for item in value)
        elif isinstance(value, dict):
            return {key: cls._mapping_child_value(val) for key, val in value.items()}
        return value

    def __update_configuration__(self, valid_data: BaseModel):
        valid_dict = valid_data.model_dump()
        for name in self.__qstd_nested_configuration_fields__:
            nested_configuration = getattr(self, name)
            valid_value = getattr(valid_data, name)
            if nested_configuration is not None\
                    and isinstance(nested_configuration, BaseConfig)\
                    and isinstance(valid_value, BaseModel):
                nested_configuration.__update_configuration__(valid_value)
            else:
                if isinstance(valid_value, BaseModel):
                    valid_dict[name] = self._mapping_child_value(valid_value)
        for attr, value in valid_dict.items():
            setattr(self, attr, value)


class MultiprocessingConfig(BaseConfig):
    """
    A configuration class that stores and manages configuration data in shared memory
    across multiple processes. This class inherits from BaseConfig and allows for
    nested configurations to be validated and mapped from raw input data, including
    access to configuration values stored in shared memory.

    Attributes:
        _multiprocessing_dict (dict): The dictionary used for shared memory storage of the configuration.
        _is_subclass (bool): Flag indicating if this instance is a subclass instance.
        _field_access_path (list): A list of strings or integers representing the path to access nested configuration.
    """
    def __init__(
        self,
        valid_data: BaseModel,
        *,
        multiprocessing_dict: typing.Optional[dict],
        is_subclass: bool = False,
        field_access_path: typing.List[typing.Union[str, int]] = None
    ):
        """
        Initializes the MultiprocessingConfig instance by mapping the provided validated
        data (from Pydantic) to the internal shared memory configuration structure, including
        nested configurations and basic fields.

        The field_access_path indicates the path to the location of the original data in shared memory
        relative to the current configuration class.

        Args:
            valid_data (BaseModel): A Pydantic validated model instance containing the configuration data.
            multiprocessing_dict (dict, optional): The dictionary for shared memory storage of configuration.
            is_subclass (bool, optional): Flag indicating if this instance is a subclass instance. Defaults to False.
            field_access_path (list, optional): A list of strings or integers representing the path to access
                nested configuration in shared memory relative to the current configuration class.
        """
        self._multiprocessing_dict = multiprocessing_dict
        self._is_subclass = is_subclass
        self._field_access_path = field_access_path or []
        if is_subclass is False:
            self._multiprocessing_dict.update(valid_data.model_dump())

        for name in self.__qstd_nested_configuration_fields__:
            access_path = list(self._field_access_path)
            access_path.append(name)
            value = self._mapping_child_value(getattr(valid_data, name), access_path)
            setattr(self, name, value)

    def __getattr__(self, name: str):
        """
        Accesses the configuration value from shared memory. This method is invoked when
        an attribute is accessed that is not explicitly defined in the instance.

        Args:
            name (str): The name of the configuration property.

        Returns:
            The configuration value from shared memory, if it exists.

        Raises:
            AttributeError: If the attribute is not found in the shared configuration.
        """
        try:
            result = object.__getattribute__(self, name)
            return result
        except AttributeError:
            configuration = self._multiprocessing_dict
            for key in self._field_access_path:
                if type(configuration) not in (list, tuple, frozenset) and key not in configuration:
                    raise AttributeError(f'{key} not found in shared configuration')
                configuration = configuration[key]
            if name in configuration:
                return configuration[name]
            raise AttributeError(f"{name} not found in shared configuration")

    def _mapping_child_value(self, value: typing.Any, field_access_path: typing.List[typing.Union[str, int]]):
        """
        Recursively replaces instances of BaseModel with instances of a configuration class
        inheriting from BaseConfig. It also handles lists, tuples, frozensets, and dicts,
        mapping each element or key to the corresponding configuration model.

        The method identifies all models and replaces them with configuration classes,
        including within nested structures.

        Args:
            value (typing.Any): The value to map, which can be a BaseModel, list, tuple, frozenset, or dict.
            field_access_path (list): The access path to this value for nested configurations.

        Returns:
            The mapped value, where instances of BaseModel are replaced with configuration class instances,
            and other types (e.g., lists, dicts) are handled appropriately.
        """
        if isinstance(value, BaseModel):
            return value.__qstd_config_cls__(
                value,
                multiprocessing_dict=self._multiprocessing_dict,
                is_subclass=True,
                field_access_path=field_access_path
            )
        elif isinstance(value, (list, tuple, frozenset)):
            result = []
            for index, item in enumerate(value):
                _field_access_path = list(field_access_path)
                _field_access_path.append(index)
                result.append(self._mapping_child_value(item, _field_access_path))
            return type(value)(result)
        elif isinstance(value, dict):
            result = {}
            for key, item in value.items():
                _field_access_path = list(field_access_path)
                _field_access_path.append(key)
                result[key] = self._mapping_child_value(item, _field_access_path)
            return result
        return value

    def __update_configuration__(self, valid_data: BaseModel):
        if self._is_subclass is False:
            self._multiprocessing_dict.update(valid_data.model_dump())
        for name in self.__qstd_nested_configuration_fields__:
            nested_configuration = getattr(self, name)
            valid_value = getattr(valid_data, name)
            if nested_configuration is not None\
                    and isinstance(nested_configuration, BaseConfig)\
                    and isinstance(valid_value, BaseModel):
                nested_configuration.__update_configuration__(valid_value)
            else:
                value = self._mapping_child_value(valid_value, list(self._field_access_path))
                setattr(self, name, value)

    def _repr_str(self):
        configuration = self._multiprocessing_dict
        for key in self._field_access_path:
            if type(configuration) not in (list, tuple, frozenset) and key not in configuration:
                raise AttributeError(f'{key} not found in shared configuration')
            configuration = configuration[key]
        return f'{type(self).__name__}({str(configuration)})'
