# Campsite

This is a flask project using a remote postgresql server to store data for the model. Currently it is hosted by Heroku. The leaflet.js library is used to add map functionality, which display the OSM tiles that the user sees. 

The purpose of this project is to showcase some web development and design pattern knowledge. The design patterns you'll see consist of, mainly:
- Model-View-Controller: a very popular pattern for web applications, used here as well. It's useful because it makes the project code better organized and easier to understand. Each part of MVC has its own file in the `website/` directory. The authentication logic has its own file `auth.py`: a common practice in an MVC implementation, since this logic does not typically fit neatly within any particular component of MVC. 
- Observer: In `website/controllers/notifications.py`, an observer has been added to handle emailing users when they are added as collaborators to a CampSite list. Future work is planned to allow these users the ability to add and remove CampSites to and from a CampSite list. 
- Proxy: In `website/static/script/marker_loader.js`, a Proxy pattern has been implemented that caches markers and lazily loads markers on the singleton leaflet. The initial concern was that the map could become very slow to load as more and more users add CampSites to the map. This at least partly addresses the problem for now. 
- Singleton: Also in `website/static/script/CampSite_map.js` is the `CampSiteMapSingleton` class, which represents the single global map object for the website. A single map instance was desired to make the map experience consistent for all users.


# Heroku

This project is hosted by Heroku and uses a Heroku Postgres database. Heroku rotates database credentials periodically, meaning the URI, user, and password may change. Therefore, anything that is hardcoded in the `.env` file may become out of date. 

Occasionally, you should run `heroku config:get DATABASE_URL --app campsite` to get the latest credentials so you can run the application locally. Run the command and update the `DATABASE_URL` field. 

This is only necessary for local testing. Heroku will automatically update these environment variables on their end. 

# Running Locally

The public facing website should be accessible here: https://campsite-c562d9081c68.herokuapp.com/

To run locally, you will need to complete the following:

1. Ensure you have Python3.10 installed. Then install requirements with: `pip install -r requirements.txt`
2. If you wish to have full interactivity with the remote database, you'll need to update the `copy.env` file with the relevant information and then rename the file to `.env`. You won't get the database URI, but you can still test fuctionality that does not require commiting or querying the database. 
3. In the root of the project run `python3 main.py`. Flask will start a local server that you can access at `localhost:5000`.

# Who is this for?

The application targets a fairly niche community of backpackers, hunters, campers, kayakers/canooers, etc. who are interested in keeping track of their favorite campsites as they enjoy their favorite outdoor recreation. 

As an avid backpacker myself, I often wish there was a better way to track my favorite camping locations other than something like a Google Maps pin. 

The problem is that there is a gap in a nice interface for doing this, and the motivation is to make one for myself and others to enjoy.
