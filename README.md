# Campsite

This is a flask project using a remote postgresql server to store data for the model. Currently it is hosted by Heroku. The leaflet.js library is used to add map functionality, which display the OSM tiles that the user sees. 

The purpose of this project is to showcase some web development and design pattern knowledge. The design patterns you'll see consist of, mainly:
- Observer: In `website/controllers/notifications.py`, an observer has been added to handle emailing users when they are added as collaborators to a CampSite list. Future work is planned to allow these users the ability to add and remove CampSites to and from a CampSite list. This could be extended in the future to a push notification, if the application were to get a mobile app version.
- Proxy: In `website/static/script/marker_loader.js`, a Proxy pattern has been implemented that caches markers and lazily loads markers on the singleton leaflet. The initial concern was that the map could become very slow to load as more and more users add CampSites to the map. This at least partly addresses the problem for now. 
- Singleton: Also in `website/static/script/map.js` is the `CampSiteMapSingleton` class, which represents the single global map object for the website. A single map instance was desired to make the map experience consistent for all users.
- Model-View-Controller: a very popular pattern for web applications, used here as well. It's useful because it makes the project code better organized and easier to understand. Each part of MVC has its own file in the `website/` directory. The authentication logic has its own file `auth.py`: a common practice in an MVC implementation, since this logic does not typically fit neatly within any particular component of MVC. 


# How to Deploy Locally

The public facing website should be accessible here: https://campsite-c562d9081c68.herokuapp.com/

If you want to run locally, you will need to complete the following:

1. Ensure you have Python3.10 installed. Then install requirements with: `pip install -r requirements.txt`
2. Configure your `copy.env`. More than likely you will not need to configure anything here, but you will need to rename it to `.env`. Make sure the `FILL_TABLES=True` is set so you can fill the database with some test data.
3. In the root of the project run `python3 main.py`. Flask will start a local server that you can access at `localhost:5000`.
4. If the `FLASK_ENV=development` is set, a local SQLite3 server will spin up at `instance/dev.db` which you can then query to see how the model behaves. You will need to make sure this is the case for local testing.
5. With the app running, navigate to `localhost:5000/filltables`. There is no template for this page so you will get a generic `404` but should see the success message below. Navigate back to the home page to see how the map has filled up with psuedo-random data. Most test campsites are generated without photos due to the costs incurred with creating so much random data. This function creates random users and campsites which you can interact with. Also, the location of campsite pins are also randomly generated within North America, but the locations might not make sense, so don't be alarmed if you see some campsites in the ocean. :) 

**NOTE: You will not be able to test functionality of the SMTP/email notification feature unless you specify your own Google account information.** For security purposes I am not willing to leave my credentials in the `copy.env`. If desired you can [view the Google article](https://support.google.com/accounts/answer/185833?hl=en) on creating an app password. In a nutshell, you will need to go to your Google account settings, enable 2FA if not already enabled, go to Security > App passwordss, then create an app password for "Mail", then finally update the `.env` file with this information. It would likely be easier to make two test accounts on the public facing website, sign in with one, then collaborate with the other account, then login to the other accounts email to see the notification. 

# Who is this for?

The application targets a fairly niche community of backpackers, hunters, campers, kayakers/canooers, etc. who are interested in keeping track of their favorite campsites as they enjoy their favorite outdoor recreation. 

As an avid backpacker myself, I often wish there was a better way to track my favorite camping locations other than something like a Google Maps pin. 

The problem is that there is a gap in a nice interface for doing this, and the motivation is to make one for myself and others to enjoy.

# Heroku

This project is hosted by Heroku and uses a Heroku Postgres database. Heroku rotates database credentials periodically, meaning the URI, user, and password may change. Therefore, anything that is hardcoded in the `.env` file may become out of date. 

Occasionally, you should run `heroku config:get DATABASE_URL --app campsite` to get the latest credentials so you can run the application locally. Run the command and update the `DATABASE_URL` field. 

This is only necessary for local testing. Heroku will automatically update these environment variables on their end. 