[app]
title = Personal Budget Tracker
package.name = budgettracker
package.domain = org.teamc
source.dir = .
source.include_exts = py,png,kv,atlas
source.exclude_patterns = test_*.py
version = 1.0.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
p4a.branch = master
[buildozer]
log_level = 2
warn_on_root = 1
