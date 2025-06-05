from setuptools import setup, find_packages

setup(
    name='HallFree',
    version='0.1.0',
    description='Factor Sums and Hall Free Partitions: Number-theoretic and combinatorial tools',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(where='.'),
    package_dir={'': '.'},
    install_requires=[
        'pytest',
        # SageMath is not pip-installable, but document as a requirement
    ],
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
    zip_safe=False,
) 