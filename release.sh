set -e

if [ "$#" -ne 1 ]; then
    printf 'missing release mode\n'
    false
elif [ "$1" = "test" ]; then
    test_release=true
elif [ "$1" = "release" ]; then
    test_release=false
else
    printf 'invalid release mode\n'
    false
fi

python setup.py sdist bdist_wheel
if $test_release; then
    twine upload --repository testpypi dist/*
else
    twine upload dist/*
fi

rm -rf build/
rm -rf dist/
rm -rf src/kitty_escape.egg-info/
