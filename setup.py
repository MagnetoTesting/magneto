from setuptools import setup, find_packages

setup(
    name='magneto',
    version='0.31.1',
    description='Magneto - Test Automation for Android',
    author='EverythingMe',
    author_email='automation@everything.me',
    url='http://github.com/EverythingMe/magneto',
    packages=find_packages(),
    install_requires=[
        'pytest',
        'pytest-ordering',
        'uiautomator',
        'futures',
        'coloredlogs',
        'IPython',
        'Click'
    ],

    entry_points={
        'console_scripts': [
            'magneto = magneto.main:main',
            'imagneto = magneto.imagneto:main'
        ]
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing'
    ]
)
