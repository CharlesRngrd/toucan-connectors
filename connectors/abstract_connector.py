from abc import ABCMeta, abstractmethod


class AbstractConnector(metaclass=ABCMeta):
    def __init__(self, **kwargs):
        if 'name' not in kwargs:
            raise MissingConnectorName
        self.name = kwargs['name']

        for required_arg in self._get_required_args():
            if required_arg not in kwargs:
                raise MissingConnectorOption(self, required_arg)
            setattr(self, required_arg, kwargs[required_arg])

        try:
            for optional_arg in self._get_optional_args():
                if optional_arg in kwargs:
                    setattr(self, optional_arg, kwargs[optional_arg])
        except NotImplementedError:
            pass

    @abstractmethod
    def _get_required_args(self):
        raise NotImplementedError

    @abstractmethod
    def _get_optional_args(self):
        raise NotImplementedError

    @abstractmethod
    def query(self, query, fields=None):
        raise NotImplementedError

    @abstractmethod
    def is_connected(self):
        raise NotImplementedError


class MissingConnectorOption(Exception):
    """ Raised when an option is missing when instantiating a connector """

    def __init__(self, connector, option):
        self.option = option
        self.msg = f'The connector "{connector.name}" misses the {option} option'

    def __str__(self):
        return repr(self.msg)


class MissingConnectorName(Exception):
    """ Raised when a connector has no given name """


class InvalidDataProvider(Exception):
    """ Raised when a data provider doesn't exist or isn't registered """

    def __init__(self, name):
        self.name = name
        self.msg = f'No data provider named "{self.name}"'

    def __str__(self):
        return repr(self.msg)


class InvalidDataProviderSpec(Exception):
    """ Raised when a data provider configuration is invalid """


class InvalidDataProviderType(InvalidDataProviderSpec):
    """ Raised when no connector exists for a type of data provider """


class InvalidDataFrameQueryConfig(Exception):
    """ Raised when the get_df config has not the expected arguments"""
