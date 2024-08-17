@echo off
docker build -t ragops-lambda .

REM Remove the container if it exists
docker rm temp-container 2>nul

docker run --name temp-container ragops-lambda
docker cp temp-container:/var/task ragops_lambda_package
docker rm temp-container

REM Use -Force to overwrite existing zip file
powershell Compress-Archive -Path ragops_lambda_package\* -DestinationPath ragops_lambda.zip -Force

rmdir /S /Q ragops_lambda_package