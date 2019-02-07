from setuptools              import setup
from setuptools.command.test import test as Test

with open('README.rst', 'r') as fp:
	for line in fp:
		if not line[:-1]: break
	readme = ''.join(line for line in fp)

class CustomTest(Test):
	user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

	def initialize_options(self):
		# In Python < 3, this is an old-style class, so no super()
		Test.initialize_options(self)
		self.pytest_args = " ".join([
			"-v",
			"--cov",
			"--cov-report term:skip-covered",
			"--cov-report annotate",
		])

	def run_tests(self):
		from shlex  import split
		from sys    import exit
		from pytest import main

		exit(main(split(self.pytest_args)))

setup(
	name='simplejsonseq',
	version='0.2.1',
	author='Alexander Shpilkin',
	author_email='ashpilkin@gmail.com',
	description='Encoder and decoder for JSON text sequences',
	long_description=readme,
	long_description_content_type='text/x-rst',
	url='https://github.com/alexshpilkin/simplejsonseq',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Topic :: Software Development :: Libraries :: Python Modules',
	],

	py_modules=['simplejsonseq'],
	python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
	install_requires=[],
	tests_require=['pytest', 'pytest-cov', 'pytest-mock'],
	cmdclass={
		'test': CustomTest,
	}
)
