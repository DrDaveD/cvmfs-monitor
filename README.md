# cvmfs-monitor

## Setting up a Development Environment (Scientific Linux 6)

* Checkout the main [CVMFS Git repository](https://github.com/cvmfs/cvmfs)
* Install the python-cvmfsutils package
	* `cd cvmfs/python && sudo python setup.py install`
	* setup.py installs dependencies automatically
	* for the reference RPM dependencies are:
		* python-dateutil
		* python-requests
		* m2crypto

* Check out [cvmfs-monitor repository](https://github.com/cvmfs/cvmfs-monitor)
* Install dependencies using either `pip` or `yum`
	* RPM dependencies are:
		* Django14
		* python-django-south (not Django-south!!)
		* python-django-tastypie

* Setup configuration for web application
	* `cd cvmfs-monitor/cvmfsweb/cvmfsweb && cp settings.py.example settings.py`
	* edit `settings.py`:
		* set ADMINS as stated
		* define an SQLite database file in DATABASES['default']['NAME']
	* setup the intial database content
		* `cd cvmfs-monitor/cvmfsweb`
		* `./manage.py sncdb` (create an admin user when asked)
		* `./manage.py migrate`

* Run a development server
	* `cd cvmfs-monitor/cvmfsweb`
	* `./manage.py runserver 0.0.0.0:8000`
	* Note potential iptable problems when accessing this server 

* Access the admin panel on
	* http://<ip.address>:8000/admin
	* username and password were defined during database setup
	* create some test data here

* Access the API
	* http://<ip.address>:8000/cvmfsmon/api/v1.0/repository/<fqrn>?format=json
