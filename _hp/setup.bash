# Update /etc/hosts (include custom hosts)
cat host-config.txt | sudo tee -a /etc/hosts

# Update apt and install dependencies
sudo apt update
sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev -y

# Browser stuff https://www.selenium.dev/documentation/selenium_manager/#browser-dependencies
sudo apt-get install libatk-bridge2.0-0
sudo apt-get install libdbus-glib-1-2
sudo apt install libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev
sudo apt-get install libasound2

# Install pyenv + python 3.11
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' | tee -a  ~/.bashrc ~/.install-conf
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' | tee -a  ~/.bashrc ~/.install-conf
echo 'eval "$(pyenv init -)"' | tee -a  ~/.bashrc ~/.install-conf
source ~/.install-conf
pyenv install 3.11

# Install poetry and requirements (with python 3.11)
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' | tee -a  ~/.bashrc ~/.install-conf
source ~/.install-conf
poetry env use 3.11
poetry install

# (Alternative) Run with pip
# pip install --user -r requirements.txt

# Grant WPT ability to bind to port 80 and 443
sudo setcap CAP_NET_BIND_SERVICE=+eip /home/ubuntu/.pyenv/versions/3.11.5/bin/python3.11