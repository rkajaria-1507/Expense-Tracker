from setuptools import setup, find_packages

setup(
    name="expense_tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "matplotlib>=3.5.0",
        "numpy>=1.20.0",
        "streamlit>=1.21.0",
        "pandas>=1.5.0",
        "plotly>=5.10.0",
    ],
    python_requires=">=3.6",
    include_package_data=True,
    package_data={
        "expense_tracker": ["static/templates/*.csv", "static/img/*.png"],
    },
    entry_points={
        "console_scripts": [
            "expense-tracker=expense_tracker.main:main",
        ],
    },
)