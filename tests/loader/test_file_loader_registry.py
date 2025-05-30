from qstd_config.loader import JsonFileLoader, YamlFileLoader, file_loader_registry


def test_file_loader_registry():
    loaders = file_loader_registry.get_file_loaders()

    assert len(loaders) == 2
    assert isinstance(loaders[0], YamlFileLoader)
    assert isinstance(loaders[1], JsonFileLoader)

    file_loader_registry.unregister_file_loader(
        lambda loader: '.yaml' in loader.supported_extensions(),
    )

    loaders = file_loader_registry.get_file_loaders()

    assert len(loaders) == 1
    assert isinstance(loaders[0], JsonFileLoader)

    file_loader_registry.register_file_loader(YamlFileLoader(), priority=1)

    loaders = file_loader_registry.get_file_loaders()

    assert len(loaders) == 2

    assert isinstance(loaders[0], YamlFileLoader)
    assert isinstance(loaders[1], JsonFileLoader)

    file_loader_registry.register_file_loader(YamlFileLoader(), priority=2)

    loaders = file_loader_registry.get_file_loaders()

    assert len(loaders) == 3

    assert isinstance(loaders[0], YamlFileLoader)
    assert isinstance(loaders[1], YamlFileLoader)
    assert isinstance(loaders[2], JsonFileLoader)

    file_loader_registry.register_file_loader(YamlFileLoader(), replace=True)

    loaders = file_loader_registry.get_file_loaders()

    assert len(loaders) == 2

    assert isinstance(loaders[0], YamlFileLoader)
    assert isinstance(loaders[1], JsonFileLoader)
