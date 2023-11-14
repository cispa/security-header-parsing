# Setting up the Android emulators for testing purposes

## Prerequisite
1. `Python` (3 are supported).
2. The current logged user must have kvm permission (https://stackoverflow.com/questions/37300811/android-studio-dev-kvm-device-permission-denied)

## How to setup the emulators
1. Run the following script to setup the environment.
```shell
python setup.py
```

2. Then, we need to run the following script to create the emulators.

```shell
python cmd_emulators.py -method init -system_image android30 -num_devices 30
```

| Parameter  | Description |
| ------------- | ------------- |
| -method  | init  |
| -system_image  | android25 or android30  |
| -num_devices  | The numbers of emulator devices |

## How to install the mobile browser
1. First, we now start our emulators up by the following script.

```shell
python cmd_emulators.py -method start -num_devices 30
```
| Parameter  | Description |
| ------------- | ------------- |
| -method  | start  |
| -num_devices  | The number of emulators devices should be less than or equal to the number of devices created in the initialization step.|
| -has_window  | By default it disables graphical window display on the emulator, turn it on by provide this parameter|


2. Second, we install the mobile browser app that we need to test. The following script shows how to install the Firefox browser app.

```shell
python cmd_emulators.py -method install -apk_file fenix-98.2.0-x86.apk -package_name org.mozilla.firefox
```

| Parameter  | Description |
| ------------- | ------------- |
| -method  | install  |
| -apk_file  | The path to the apk file of the browser app  |
| -package_name  | The package name of the browser app  |