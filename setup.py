import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="laet-timetable-parser", # Replace with your own username
    version="0.0.5",
    author="Giancarlo Grasso",
    author_email="giancarlo.grasso@laetottenham.ac.uk",
    description="A parser for adding timetables from bromcom to google calendar",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[
        'pytz',
        'icalendar',
        'pandas',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        "gui_scripts": [
            'laet_timetable_parser = laet_timetable_parser.gui:main' 
        ]
    },
)
