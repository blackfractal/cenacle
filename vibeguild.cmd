@echo off
setlocal
pushd "%~dp0"
python -m vibeguild %*
popd
