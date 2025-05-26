from setuptools import find_packages, setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='qstd_config',
    version='1.0.0',
    author='QuisEgoSum',
    author_email='subbotin.evdokim@gmail.com',
    description='Application configuration manager',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/QuisEgoSum/qstd-config',
    packages=find_packages(exclude=['example', '*test*']),
    install_requires=[
        'pydantic>=2.0.0',
        'PyYAML>=6.0',
    ],
    keywords='config yaml env',
    python_requires='>=3.9',
    license='MIT',
    include_package_data=False
)
