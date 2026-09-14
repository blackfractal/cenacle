@echo off
setlocal
pushd "%~dp0"
python -m cenacle --home "%~dp0.local\runtime" serve --browser %*
popd
