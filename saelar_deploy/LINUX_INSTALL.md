# SAELAR – Linux one-command install

## 1. Copy the distro to the Linux box

Copy **SAELAR-distro-YYYYMMDD.zip** (and optionally this folder’s `install_saelar` and `install saelar` if you’re not using the zip) to the target machine.

## 2. Install (one command)

**Option A – from the zip (recommended)**

```bash
unzip SAELAR-distro-*.zip
chmod +x install_saelar "install saelar"
./install_saelar
```

Or literally:

```bash
./install saelar
```

**Option B – run from anywhere**

1. Add the extracted folder to `PATH`, e.g.:

   ```bash
   export PATH="$PATH:/path/to/extracted/dir"
   ```

2. Run:

   ```bash
   install_saelar
   ```
   or  
   ```bash
   "install saelar"
   ```

## 3. Start SAELAR

```bash
cd SAELAR   # or the dir where install_saelar put the app
./start_saelar.sh
```

Port defaults to **8484**; override with `SAELAR_PORT=8080 ./start_saelar.sh` if needed.

## What the installer does

- **Fresh install:** If installing from zip, removes any existing `SAELAR/` directory first so the new distro is clean.
- **Optional:** If a previous SAELAR install is found at `/opt/apps` (e.g. from EC2), prompts to remove it for a clean system install.
- **Cache cleanup:** Removes `__pycache__` and `.streamlit` cache in the app directory so old code/cache doesn’t affect the new run.
- Finds **SAELAR-distro-*.zip** in the script directory or current directory; if found, unzips into `SAELAR/`.
- If no zip, uses the current directory if it already contains `nist_setup.py` and `requirements.txt`.
- Installs dependencies with `pip3 install -r requirements.txt`.
- Creates **start_saelar.sh** in the app directory.

## Requirements on the Linux box

- **Python 3.8+** (`python3`)
- **pip** (`pip3` or `python3 -m pip`)
- **unzip**
