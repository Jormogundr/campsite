# Campsite

The current implementation for this project uses a postgresql server to store data for the model. You should specifiy the the `DATABASE_URL` in the `copy.env` file, then rename it to be just `.env` so that the program can parse your variables. 

The purpose of this project is to showcase some web development and design pattern knowledge. The design patterns you'll see consist of, mainly:
- Model-View-Controller: a very popular pattern for web applications, used here as well. It's useful because it makes the project code better organized and easier to understand. Each part of MVC has its own file in the `website/` directory. The authentication logic has its own file `auth.py`: a common practice in an MVC implementation, since this logic does not typically fit neatly within any particular component of MVC. 