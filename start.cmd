@echo off
setlocal
pushd "%~dp0"
python -m vibeguild --home "%~dp0.local\runtime" serve --browser %*
popd
