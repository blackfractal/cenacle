@echo off
setlocal
pushd "%~dp0"
python -m cenacle %*
popd
