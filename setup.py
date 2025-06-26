#!/usr/bin/env python3
"""
Setup configuration for SecureVault
"""
from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="securevault",
    version="1.0.0",
    author="SecureVault Contributors",
    author_email="contact@securevault.dev",
    description="🔐 Enterprise-grade password manager that keeps your secrets... secret.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/securevault",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/securevault/issues",
        "Source": "https://github.com/yourusername/securevault",
        "Documentation": "https://securevault.dev/docs",
        "Security": "https://github.com/yourusername/securevault/security",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Topic :: Security :: Cryptography",
        "Topic :: Security",
        "Topic :: System :: Systems Administration :: Authentication/Directory",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-benchmark>=3.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.900",
            "bandit>=1.7",
            "safety>=2.0",
            "pre-commit>=2.0",
        ],
        "docker": [
            "gunicorn>=20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "securevault=app.cli:main",
            "securevault-web=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["templates/*", "static/*"],
    },
    keywords=[
        "password-manager",
        "security",
        "cryptography",
        "encryption",
        "credentials",
        "vault",
        "privacy",
        "zero-knowledge",
        "self-hosted",
        "offline",
    ],
    zip_safe=False,
)
