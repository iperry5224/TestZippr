@echo off
cd /d c:\Users\iperr\TestZippr
set EC2_HOST=%SOPRA_EC2_HOST%
if "%EC2_HOST%"=="" set EC2_HOST=ec2-user@18.232.122.255
echo Building zip...
python create_sopra_ec2_update.py
if errorlevel 1 exit /b 1
echo Copying to EC2 (%EC2_HOST%)...
scp -i saelar-sopra-key.pem -o ConnectTimeout=60 sopra_ec2_update.zip %EC2_HOST%:~/sopra_ec2_update.zip
if errorlevel 1 (
    echo SCP failed. Ensure VPN is connected.
    exit /b 1
)
echo Deploying on EC2...
ssh -i saelar-sopra-key.pem -o ConnectTimeout=60 %EC2_HOST% "cd ~; pkill -f 'streamlit run sopra_setup' 2>/dev/null || true; sleep 1; unzip -o sopra_ec2_update.zip; chmod +x start_sopra.sh 2>/dev/null || true; nohup ./start_sopra.sh > /tmp/sopra.log 2>&1 & sleep 2; echo SOPRA restarted on 8180"
echo Done.
