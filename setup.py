from datetime import datetime
from subprocess import check_output, CalledProcessError
from warnings import warn

from setuptools import setup, find_packages


def version():
    date_string = datetime.now().strftime("1.%Y%m%d.%H%M%S")
    try:
        git_sha = check_output(["git", "describe", "--always", "--dirty=dirty", "--match=NOTHING"]).strip().decode()
        return "{}+{}".format(date_string, git_sha)
    except (CalledProcessError, OSError) as e:
        warn("Error calling git: {}".format(e))
    return date_string


GENERIC_REQ = [
    "k8s==0.10.0",
    "ConfigArgParse==0.13.0",
    "six==1.10.0",
    "PyYAML==3.13",
    "pyaml==17.12.1",
    "prometheus_client==0.4.0",
    'requests==2.13.0',
]

WEB_REQ = [
    "Flask==1.0.2",
    "flask-talisman==0.5.1",
    "blinker==1.4",
    "flask-bootstrap==3.3.7.1",
    "flask-nav==0.6",
    "dominate==2.3.4",
    "gevent == 1.3.7",
]

CODE_QUALITY_REQ = [
    'prospector',
]

TESTS_REQ = [
    'mock==2.0.0',
    'pytest-html==1.19.0',
    'pytest-cov==2.6.0',
    'pytest-helpers-namespace==2017.11.11',
    'pytest==3.8.2',
    'requests-mock==1.5.2'
]

CI_REQ = [
    'tox',
    'tox-travis',
]

setup(
    name="fiaas-skipper",
    url="https://github.com/fiaas/skipper",
    author="FIAAS developers",
    author_email="fiaas@googlegroups.com",
    version=version(),
    packages=find_packages(exclude=("tests",)),
    zip_safe=False,
    # Requirements
    install_requires=GENERIC_REQ + WEB_REQ,
    setup_requires=['pytest-runner', 'wheel', 'setuptools_scm'],
    extras_require={
        "dev": TESTS_REQ + CODE_QUALITY_REQ + CI_REQ,
        "ci": CI_REQ,
        "codacy": ["codacy-coverage"],
    },
    tests_require=TESTS_REQ,
    entry_points={"console_scripts": ['skipper=fiaas_skipper:main']},
    include_package_data=True,
)
