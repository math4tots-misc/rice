@type %~1 | python %~dp0\..\rice.py > a.cc && g++ -Wall -Werror -Wpedantic -Wextra --std=c++14 a.cc && a.exe
