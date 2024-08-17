@echo off
docker build -t ragops-lambda .
docker run --name temp-container ragops-lambda
docker cp temp-container:/var/task ragops_lambda_package
docker rm temp-container
powershell Compress-Archive -Path ragops_lambda_package\* -DestinationPath ragops_lambda.zip
rmdir /S /Q ragops_lambda_package