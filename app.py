from dotenv import load_dotenv 
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import ProductionConfig

from chefs_kitchen.db import db
from chefs_kitchen.models.chef_model import Chef
from chefs_kitchen.models.kitchen_model import KitchenModel
from chefs_kitchen.models.user_model import Users
from chefs_kitchen.utils.logger import configure_logger

def create_app(config_class=ProductionConfig) -> Flask:
    """Creates a Flask application

    Args:
        config_class (Config): The configuration class to use.

    Returns:
        Flask app: The Flask application with the specfied configuration.

    """
    app = Flask(__name__)
    configure_logger(app.logger)

    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.filter_by(username=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        return make_response(jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401)

    kitchen_model = KitchenModel()

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        return make_response()
    
    ##########################################################
    #
    # User Management
    #
    ##########################################################

    @app.route('/api/create-user', methods=['PUT'])
    def create_user() -> Response:
        """Route to register a new user account.

        Expected JSON Input:
            - username (str): The desired username.
            - password (str): The desired password.

        Returns:
            A JSON response indicating the success of the user creation.

        Raises:
            400 error if the username or password is missing.
            500 error if there is an issue creating the user in the database.

        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            Users.create_user(username, password)
            return make_response(jsonify({
                "status": "success",
                "message": f"User '{username}' created successfully"
            }), 201)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"User creation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating user",
                "details": str(e)
            }), 500)
    
    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """Route to authenticate a user and then log them in.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The password of the user.

        Returns:
            A JSON response indicating the success of the login attempt.

        Raises:
            401 error if the username or password is incorrect.

        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                return make_response(jsonify({
                    "status": "success",
                    "message": f"User '{username}' logged in successfully"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid username or password"
                }), 401)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 401)
        except Exception as e:
            app.logger.error(f"Login failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred during login",
                "details": str(e)
            }), 500)

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout() -> Response:
        """Route to log out the current user.

        Returns:
            A JSON response indicating the success of the logout operation.

        """
        logout_user()
        return make_response(jsonify({
            "status": "success",
            "message": "User logged out successfully"
        }), 200)

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def change_password() -> Response:
        """Route to change the password for the current user.

        Expected JSON Input:
            - new_password (str): The new password to set.

        Returns:
            A JSON response indicating the success of the password change.

        Raises:
            400 error if the new password is not provided.
            500 error if there is an issue updating the password in the database.

        """
        try:
            data = request.get_json()
            new_password = data.get("new_password")

            if not new_password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "New password is required"
                }), 400)

            username = current_user.username
            Users.update_password(username, new_password)
            return make_response(jsonify({
                "status": "success",
                "message": "Password changed successfully"
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Password change failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing password",
                "details": str(e)
            }), 500)

    @app.route('/api/reset-users', methods=['DELETE'])
    def reset_users() -> Response:
        """A route to recreate the users table in order to delete all users.

        Returns:
            A JSON response indicating the success of recreating the Users table.

        Raises:
            500 error if there is an issue recreating the Users table.

        """
        try:
            app.logger.info("Received request to recreate Users table")
            with app.app_context():
                Users.__table__.drop(db.engine)
                Users.__table__.create(db.engine)
            app.logger.info("Users table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Users table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Users table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Chef Management
    #
    ##########################################################

    @app.route('/api/chef/create-chef', methods=['POST'])
    def create_chef() -> Response:
        """Route to create a new chef.
        
        Expected JSON Input:
            - name (str): The chef's name.
            - specialty (str): The chef's culinary specialty.
            - years_experience (int): The years of experience the chef has currently.
            - signature_dishes (int): The amount of signature dishes the chef has.
            - age (int): The age of the chef.

        Returns:
            A JSON response of successful chef creation. 

        RAISES: 
            400 error if input validation fails.
            500 error if there is an issue creating the chef to the database.      
        """
        app.logger.info("Recieved request to create a new chef.")

        try:
            data = request.get_json()

            required_fields = ["name", "specialty", "years_experience", "signature_dishes", "age"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)
            
            name = data["name"]
            specialty = data["specialty"]
            years_experience = data["years_experience"]
            signature_dishes = data["signature_dishes"]
            age = data["age"]

            if {
                not isinstance(name, str)
                or not isinstance(specialty, str)
                or not isinstance(years_experience, int)
                or not isinstance(signature_dishes, int)
                or not isinstance(age, int)
            }:
                app.logger.warning("Invalid input data types.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid input types: name/specialty should be a string, years_experience/signature_dishes/age should be integers."
                }), 400)
            
            app.logger.info(f"Adding chef: {name}, specialty in {specialty}, {years_experience} years of experience, {signature_dishes} signature dishes, {age} years old.")
            Chef.create_chef(name, specialty, years_experience, signature_dishes, age)

            app.logger.info(f"Chef created successfully: {name}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Chef '{name}' created successfully."
            }), 201)
        
        except Exception as e:
                app.logger.error(f"Failed to create chef: {e}")
                return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating the chef.",
                "details": str(e)
            }), 500)        
    
    @app.route('/api/chef/get-chef/<int:chef_id>', methods=['GET'])
    def get_chef_by_id(chef_id:int) -> Response:
        """Route to get a chef by their ID.
        
        Path Parameter: 
            - chef_id (int): The ID of the chef.

        Returns:
            A JSON response containing the chef details, if found.

        Raises: 
            400 error if the chef is not found:
            500 error is there is an issue retrieving the chef from the database.

        """
        try: 
            app.logger.info(f"Recieved request to retrieve chef with ID {chef_id}.")

            chef = Chef.get_chef_by_id(chef_id)

            if not chef:
                app.logger.warning(f"Chef with ID {chef_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Chef with ID {chef_id} not found."
                }), 400)

            app.logger.info(f"Successfully retrieved Chef: {chef}")
            return make_response(jsonify({
                "status": "success",
                "chef": chef
            }), 200)

        except Exception as e:
            app.logger.error(f"Error retrieving chef with ID {chef_id}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the chef",
                "details": str(e)
            }), 500)
 
    @app.route('/api/chef/delete-chef/<int:chef_id>', methods=['DELETE'])
    def delete_chef(chef_id:int) -> Response:
        """Route to delete a chef by id.
        
        Path Parameter: 
            - chef_id (int): The ID of the chef.

        Returns:
            A JSON response indicating successful deletion of chef details, if found.

        Raises: 
            400 error if the chef is not found:
            500 error is there is an issue removing the chef from the database.
        
        """
        try: 
            app.logger.info(f"Recieved request to delete chef with ID {chef_id}.")

            # A check to see if chef exists before attempting to delete.
            chef = Chef.get_chef_by_id(chef_id)

            if not chef:
                app.logger.warning(f"Chef with ID {chef_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Chef with ID {chef_id} not found."
                }), 400)

            Chef.delete_chef(chef_id)
            app.logger.info(f"Successfully deleted chef with ID {chef_id}.")
            return make_response(jsonify({
                "status": "success",
                "message": f"Chef with ID {chef_id} deleted successfully."
            }), 200)

        except Exception as e:
            app.logger.error(f"Error deleting chef with ID {chef_id}: {e}.")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting the chef.",
                "details": str(e)
            }), 500)
            
    ##########################################################
    #
    # Kitchen Management
    #
    ##########################################################

    @app.route('/api/kitchen/enter-chef', methods=['POST'])
    def enter_chef() -> Response:
        """Route to add an existing chef to the kitchen.
        
        Expected JSON Input:
            - chef_name (str): The chef's name.

        Returns:
            A JSON response indicating success of entering chef to kitchen.

        Raises:
            400 error if required field is missing or the chef does not exist.
            500 error if there is an issue entering the chef to the kitchen.
            
        """
        try:
            data = request.get_json()
            chef_name = data.get("name")

            if not chef_name:
                app.logger.warning("Attempted to enter chef without specifying a chef.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Must specify a chef."
                }), 400)
            
            app.logger.info(f"Recieved request to enter Chef {name} to kitchen.")

            # A check to see if chef exists, before attempting to enter them into kitchen.
            chef = Chef.get_chef_by_name(chef_name)
            
            if not chef:
                app.logger.warning(f"Chef {chef_name} is not found in database.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Chef {chef_name} not found." 
                }), 400)
            
            try: 
                kitchen_model.enter_kitchen(chef)
            except ValueError as e:
                app.logger.warning(f"Cannot enter {chef_name}: {e}")
                return make_response(jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400)
            
            chefs = kitchen_model.get_chefs()

            app.logger.info(f"Chef '{chef_name}' entered the kitchen. Current chefs: {chefs}.")

            return make_response(jsonify({
                "status": "success",
                "message": f"Chef '{chef_name}' is now in the kitchen.",
                "chefs": chefs
            }), 200)
        
        except Exception as e:
            app.logger.error(f"Failed to enter chef into the kitchen: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while entering the chef into the kitchen",
                "details": str(e)
            }), 500)
    
    @app.route('/api/kitchen/cookoff', methods=['POST'])
    def cookoff() -> Response:
        """Route that triggers a cookoff between the current chefs.
        
        Returns: A JSON response indicating the winner of the cookoff.

        Raises:
            400 error if the cookoff cannot be triggered due to insufficient number of chefs.
            500 error is there is an issue during the cookoff.

        """
        try: 
            app.logger.ifo("Initiaing cookoff...")

            winner = kitchen_model.fight()

            app.logger.info(f"Cookoff complete. Winner is Chef {winner}.")
            return make_response(jsonify({
                "status": "success",
                "message": "Cookoff complete",
                "winner": winner
            }), 200)
        
        except ValueError as e:
            app.logger.warning(f"Cookoff cannot be triggered: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        
        except Exception as e:
            app.logger.error(f"Error while triggering cookoff: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while triggering the cookoff.",
                "details": str(e)
            }), 500)
    
    @app.route('/api/kitchen/get-all-chefs', methods=['GET'])
    def get_all_chefs() -> Response:
        """Route that retrieves all of the current chefs in the kitchen.
        
        Returns: 
            A JSON response with the list of chefs.

        Raises:
            500 error if there is an issue getting the chefs.
        
        """
        try:
            app.logger.info("Retrieving the list of chefs in the kitchen...")

            chefs = kitchen_model.get_chefs()

            app.logger.info(f"Retrieved {len(chefs)} chefs.")
            return make_response(jsonify({
                "status": "success",
                "chefs": chefs
            }), 200)
        
        except Exception as e:
            app.logger.error(f"Failure to retreive chefs: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occured while retrieving chefs.",
                "details": str(e)
            }), 500)

    @app.route('/api/kitchen/clear-kitchen', methods=['POST'])
    def clear_kitchen() -> Response: 
        """Route to clear the list of chefs in kitchen.
        
        Returns:
            A JSON response indicating success of the operation.

        Raises:
            500 error if there is an issue clearing boxers.

        """
        try:
            app.logger.info("Clearing all chefs...")

            kitchen_model.clear_kitchen()

            app.logger.info("Chefs cleared from kitchen successfully.")
            return make_response(jsonify({
                "status": "success",
                "message": "Chefs have been cleared from kitchen."
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to clear chefs: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while clearing chefs",
                "details": str(e)
            }), 500)
       
    ##########################################################
    #
    # Leaderboard
    #
    ##########################################################

    @app.route('/api/leaderboard', methods=['GET'])
    def get_leaderboard() -> Response:
        """Route to get leaderboard of chefs sorted by cookoff wins or win percentage.
        
        Query Parameters:
            - sort (str): The key to sort by ('wins' or 'win_pct'). Default = 'wins'.

        Returns:
            A JSON response with a sorted leaderboard of chefs.

        Raises:
            400 error if an invalid sort key is provided.
            500 error if there is an issue generating the leaderboard.

        """
        try:
            sort_key = request.args.get('sort', 'wins').lower()

            valid_sort_keys = {'wins', 'win_pct'}

            if sort_key not in valid_sort_keys:
                app.logger.warning(f"Invalid sort key: {sort_key}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Invalid sort key '{sort_key}. Must be one of: {', '.join(valid_sort_keys)}"
                }), 400)
            
            app.logger.info(f"Generating leaderboard sorted by '{sort_key}'")

            leaderboard_data = Chef.get_leaderboard(sort_key)

            app.logger.info(f"Successfully generated chef leaderboard of {len(leaderboard_data)} chefs.")
            return make_response(jsonify({
                "status": "success",
                "leaderboard": leaderboard_data
            }), 200)
        
        except Exception as e:
            app.logger.error(f"Failure to generate chef leaderboard: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occured while generating the leaderboard",
                "details": str(e)
            }), 500)

    return app

if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        app.logger.error(f"Flask app encountered an error: {e}")
    finally:
        app.logger.info("Flask app has stopped.")