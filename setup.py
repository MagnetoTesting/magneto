from setuptools import setup, find_packages

setup(
    name='magneto',
    version='0.36.1',
    description='Magneto - Test Automation for Android',
    author='EverythingMe',
    author_email='automation@everything.me',
    url='http://github.com/EverythingMe/magneto',
    packages=find_packages(),
    install_requires=[
        'pytest==2.7.2',
        'uiautomator==0.1.35',
        'futures==3.0.3',
        'IPython==3.2.1',
        'Click==4.1'
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
