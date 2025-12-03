import setuptools
import pathlib


setuptools.setup(
    name='mars',
    version='1.8.3',
    description='Open world game for situated inductive reasoning.',
    url='https://github.com/XiaojuanTang/Mars',
    long_description=pathlib.Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    packages=['mars'],
    package_data={'mars': ['*.yaml', 'assets/*', 'api/*']},
    entry_points={'console_scripts': ['mars=mars.run_gui:main']},
    install_requires=[
        'imageio', 'pillow', 'opensimplex', 'ruamel.yaml', 'pyyaml', 'graphviz', 'pygame', 'gym', 'opencv-python','numpy'
    ],
    extras_require={'gui': ['pygame']},
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)
