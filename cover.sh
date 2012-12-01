PYTHONPATH=../lib/python2.7/site-packages coverage run --branch --source yieldpoints/__init__.py /Users/emptysquare/.virtualenvs/yieldpoints/bin/nosetests -vs
rm -rf html
coverage html -d html
