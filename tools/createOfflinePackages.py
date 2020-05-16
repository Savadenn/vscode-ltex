#!/usr/bin/python

import json
import os
import shlex
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

import semver



ltexRootDirPath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
libDirPath = os.path.join(ltexRootDirPath, "lib")

# to get proper logs in Travis CI
oldPrint = print
print = (lambda *args, **kwargs: oldPrint(*args, **kwargs, flush=True))



def cleanLibDir():
  cmd = ["git", "-C", ltexRootDirPath, "clean", "-f", "-x", libDirPath]
  print("Cleaning lib/ by running '{}'...".format(" ".join(shlex.quote(x) for x in cmd)))
  subprocess.run(cmd)



def getLtexVersion():
  with open(os.path.join(ltexRootDirPath, "package.json"), "r") as f: packageJson = json.load(f)
  return semver.VersionInfo.parse(packageJson["version"])

def getLatestCompatibleLtexLsVersion(versions):
  ltexVersion = getLtexVersion()
  latestVersion = None

  for version in versions:
    if semver.VersionInfo.isvalid(version):
      version = semver.VersionInfo.parse(version)

      if (version <= ltexVersion) and ((latestVersion is None) or (version > latestVersion)):
        latestVersion = version

  return latestVersion

def downloadLtexLs():
  releasesUrl = "https://api.github.com/repos/valentjn/ltex-ls/releases"
  print("Fetching list of ltex-ls releases from '{}'...".format(releasesUrl))
  with urllib.request.urlopen(releasesUrl) as f: releases = json.load(f)

  ltexLsVersion = getLatestCompatibleLtexLsVersion([x["tag_name"] for x in releases])
  print("Latest compatible release is 'ltex-ls-{}'.".format(ltexLsVersion))

  ltexLsUrl = ("https://github.com/valentjn/ltex-ls/releases/download/"
      "{0}/ltex-ls-{0}.tar.gz").format(ltexLsVersion)
  ltexLsArchivePath = os.path.join(libDirPath, "ltex-ls-{}.tar.gz".format(ltexLsVersion))
  print("Downloading ltex-ls from '{}' to '{}'...".format(ltexLsUrl, ltexLsArchivePath))
  urllib.request.urlretrieve(ltexLsUrl, ltexLsArchivePath)

  print("Extracting ltex-ls archive...")
  with tarfile.open(ltexLsArchivePath, "r:gz") as f: f.extractall(path=libDirPath)

  print("Removing ltex-ls archive...")
  os.remove(ltexLsArchivePath)



def removeJava():
  path = os.path.join(libDirPath, "jdk-11.0.7+10-jre")

  if os.path.isdir(path):
    print("Removing old Java directory '{}'...".format(path))
    shutil.rmtree(path)

  path = os.path.join(libDirPath, "._jdk-11.0.7+10-jre")

  if os.path.isfile(path):
    print("Removing old Java file '{}'...".format(path))
    os.remove(path)

def downloadJava(platform, arch):
  javaArchiveType = ("zip" if platform == "windows" else "tar.gz")
  javaArchiveName = "OpenJDK11U-jre_{}_{}_hotspot_11.0.7_10.{}".format(
      arch, platform, javaArchiveType)

  javaUrl = ("https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/"
      "jdk-11.0.7%2B10/{}").format(javaArchiveName)
  javaArchivePath = os.path.join(libDirPath, javaArchiveName)
  print("Downloading Java from '{}' to '{}'...".format(javaUrl, javaArchivePath))
  urllib.request.urlretrieve(javaUrl, javaArchivePath)
  print("Extracting Java archive...")

  if javaArchiveType == "zip":
    with zipfile.ZipFile(javaArchivePath, "r") as f: f.extractall(path=libDirPath)
  else:
    with tarfile.open(javaArchivePath, "r:gz") as f: f.extractall(path=libDirPath)

  print("Removing Java archive...")
  os.remove(javaArchivePath)



def createPackage(platform=None, arch=None):
  ltexVersion = getLtexVersion()

  if platform is None:
    packageName = "vscode-ltex-{}.vsix".format(ltexVersion)
  else:
    packageName = "vscode-ltex-{}-offline-{}-{}.vsix".format(ltexVersion, platform, arch)

  cmd = ["vsce", "package", "-o", packageName]
  print("Creating package by running '{}'...".format(" ".join(shlex.quote(x) for x in cmd)))
  subprocess.run(cmd)



def main():
  for platform, arch in [("linux", "x64"), ("mac", "x64"), ("windows", "x64")]:
    print("")
    print("Processing platform '{}' and architecture '{}'...".format(platform, arch))
    cleanLibDir()
    downloadLtexLs()
    downloadJava(platform, arch)
    createPackage(platform, arch)



if __name__ == "__main__":
  main()
