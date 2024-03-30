from setuptools import setup, find_packages


def readme():
    with open('README.md', 'r') as f:
        return f.read()


setup(
    name='qstd_config',
    version='0.1.0',
    author='QuisEgoSum',
    author_email='subbotin.evdokim@gmail.com',
    description='Application configuration manager',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/QuisEgoSum/qstd-config',
    packages=find_packages(exclude=['tmp', 'example', '*test*']),
    install_requires=[
        'pydantic==1.10.0',
        'PyYAML==6.0',
        'jsonref==0.2'
    ],
    keywords='config yaml env',
    python_requires='>=3.7',
    license='MIT',
    include_package_data=False
)
