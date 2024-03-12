# Unit Testing Folder Structure

root
    |
    --- app_test
                |
                --- test_models.py
              
# Integration Testing Folder Structure

root
    |
    --- app_test
                |
                --- frontend
                            |
                             --- test_listing.py
                             |
                             --- test_login.py
                             |
                             --- test_registration.py
                             |
                             --- test_user_update.py
                             
test_listing tests the listing creation and updates frontend:
- `test_create_listing_input_success(self, *_)`     : Input Partitioning
- `test_create_listing_boundary_success(self, *_)`  : Input Boundary Testing
- `test_create_listing_output_success(self, *_)`    : Output Partitioning

test_login tests the user login frontend:
- `test_create_listing_input_success(self, *_)`     : Input Partitioning
- `test_login_requirements_success(self, *_)`       : Requirements Partitioning
- `test_login_output_success(self, *_)`             : Output Partitioning

test_registration tests the user registration frontend:
- `test_register_input_success(self, *_)`           : Input Partitioning
- `test_register_boundary_success(self, *_)`        : Input Boundary Testing
- `test_register_output_success(self, *_)`          : Output Partitioning

test_user_update tests the user update frontend:
- `test_update_user_input(self, *_)`                : Input Partitioning
- `test_update_boundaries(self, *_)`                : Input Boundary Testing
- `test_update_output(self, *_)`                    : Output Partitioning
