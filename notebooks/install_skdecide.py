import glob
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys

try:
    from IPython import get_ipython
except ImportError:
    on_colab = False
else:
    on_colab = "google.colab" in str(get_ipython())

if on_colab:
    def subprocess_run(args):
        """So that subprocess.run displays something during subprocess on colab."""
        process = subprocess.Popen(args, stdout=subprocess.PIPE)#, stderr=subprocess.STDOUT)
        while True:
            stdout_line = process.stdout.readline().decode()
            if not stdout_line:
                break
            else:
                print(stdout_line.strip())
else:
    subprocess_run = subprocess.run

def install_skdecide(using_nightly_version=True, force_reinstall=False):
    if "scikit-decide" in [x.name for x in importlib.metadata.distributions()]:
        if force_reinstall:
            # we rather uninstall scikit-decide that use --force-reinstall flag to avoid reinstalling also all dependencies
            subprocess_run(["python", "-m", "pip", "uninstall", "scikit-decide", "-y"])
        else:
            print(
                "Scikit-decide is already installed and we are asked not to forcibly reinstall it."
            )
            return



    if using_nightly_version:
        # remove previous installation
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("release.zip"):
            os.remove("release.zip")
        # look for nightly build download url
        release_curl_res = subprocess.run(
            [
                "curl",
                "-L",
                "-k",
                "-s",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "X-GitHub-Api-Version: 2022-11-28",
                "https://api.github.com/repos/airbus/scikit-decide/releases/tags/nightly",
            ],
            capture_output=True,
        )
        release_dict = json.loads(release_curl_res.stdout)
        release_download_url = sorted(
            release_dict["assets"], key=lambda d: d["updated_at"]
        )[-1]["browser_download_url"]
        print(release_download_url)

        # download and unzip
        subprocess_run(["wget", "--output-document=release.zip", release_download_url])
        subprocess_run(["unzip", "-o", "release.zip"])

        # get proper wheel name according to python version and platform used
        wheel_pythonversion_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
        translate_platform_name = {
            "Linux": "manylinux",
            "Darwin": "macosx",
            "Windows": "win",
        }
        platform_name = translate_platform_name[platform.system()]
        machine_name = platform.machine()
        wheel_path = glob.glob(
            f"dist/scikit_decide*{wheel_pythonversion_tag}*{platform_name}*{machine_name}.whl"
        )[0]

        skdecide_pip_spec = f"{wheel_path}[all]"
    else:
        skdecide_pip_spec = "scikit-decide[all]"

    if on_colab:
        # uninstall google protobuf conflicting with ray and sb3
        subprocess_run(["python", "-m", "pip", "uninstall", "-y", "protobuf"])

    # install scikit-decide with all extras
    subprocess_run(
        ["python", "-m", "pip", "--default-timeout=1000", "install", skdecide_pip_spec]
    )

    if on_colab:
        # be sure to load the proper cffi (downgraded compared to the one initially on colab)
        import cffi

        importlib.reload(cffi)


if __name__ == "__main__":
    install_skdecide(using_nightly_version=True, force_reinstall=True)
