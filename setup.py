from setuptools import setup, find_packages

setup(
    name='queuectl',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'filelock>=3.12.0',
    ],
    entry_points={
        'console_scripts': [
            'queuectl=queuectl.main:main',
        ],
    },
    python_requires='>=3.7',
)
