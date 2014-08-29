#!/usr/bin/env bash
WD=`pwd`
cd $1
echo "Starting installation of StochSS dependencies." >> run_mac_install.log
echo "old_wd=$WD script=$0 wd=$1" >> run_mac_install.log
MY_PATH="`pwd`"              # relative
MY_PATH="`( cd \"$MY_PATH\" && pwd )`"  # absolutized and normalized
STOCHSS_HOME=$MY_PATH
STOCHSS_HOME="`( cd \"$STOCHSS_HOME\" && pwd )`" 


#################

function check_for_lib {
    if [ -z "$1" ];then
        return 1 #False
    fi
    RET=`python -c "import $1" 2>/dev/null`
    RC=$?
    if [[ $RC != 0 ]];then
        return 1 #False
    fi
    return 0 #True
}

function install_lib {
    if [ -z "$1" ];then
        return 1 #False
    fi
    export ARCHFLAGS='-Wno-error=unused-command-line-argument-hard-error-in-future'
    CMD="sudo pip install $1"
    echo $CMD >> run_mac_install.log
    eval $CMD
}

function check_and_install_dependencies {
    if ! check_pip;then
        install_pip
    fi
    deps=("numpy" "scipy" "matplotlib" "h5py")
    for dep in "${deps[@]}"
    do
        echo "Checking for $dep" >> run_mac_install.log
        if check_for_lib "$dep";then
            echo "$dep detected successfully." >> run_mac_install.log
        else
            install_lib "$dep"
            if check_for_lib "$dep";then
                echo "$dep installed successfully." >> run_mac_install.log
            else
                echo "$dep install failed." >> run_mac_install.log
                return 1 #False
            fi
        fi
    done
    return 0 #True
}

function check_pip {
    if which pip > /dev/null;then
        echo "pip is installed on your system, using it." >> run_mac_install.log
        return 0 #True
    else
        echo "pip is not installed on your system." >> run_mac_install.log
        return 1 #False
    fi
}

function install_pip {
    CMD="curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py"
    echo $CMD >> run_mac_install.log
    eval $CMD
    CMD="sudo python get-pip.py"
    echo $CMD >> run_mac_install.log
    eval $CMD
}

check_and_install_dependencies
