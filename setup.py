from setuptools import setup, find_packages

setup(
    name="fintech",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "yfinance>=0.2.0",
            "nselib>=1.9",  # NSE India official data - primary source
            "python-dateutil>=2.8.0",
        "pyarrow>=10.0.0",  # for parquet support
        "scikit-learn>=1.3.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "python-multipart>=0.0.6",
        "TA-Lib>=0.4.0",  # Note: Requires system TA-Lib library installation
        "nsepy>=0.8.0",   # Free India-oriented NSE data provider (optional)
        "pandas-market-calendars>=4.4.0",  # Trading calendars (XNSE) for continuous dates
    ],
    python_requires=">=3.8",
    author="NiftySignal Team",
    description="ML-Powered Trading Recommendations for NIFTY 50 stocks",
)