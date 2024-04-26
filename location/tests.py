import logging
import string
from typing import OrderedDict

from django.core.exceptions import ValidationError
from django.test import TestCase
from faker import Faker

from .models import Address

logger = logging.getLogger(__name__)
fake = Faker(locale="en_US")
fake.seed_locale(locale="en_US")


class AddressModelTest(TestCase):
    """
    This test case is used to test the functionality of the Address model. It includes various test methods to validate the
    behavior of the model's fields, data validation, and uniqueness constraints.

    The Address model represents a physical address and contains fields such as address_alphanumeric, predirabbrev,
    streetname, streettypeabbrev, postdirabbrev, internal, location, stateabbrev, zip, and zip4. These fields are used
    to store different components of an address.

    The test methods in this class cover different aspects of the Address model, including string representation, creation,
    required fields, unique constraint, and field validations.
    """

    # The following class variables are used to define the probabilities of the different address components being blank or
    # containing a value. The probabilities are used to generate fake addresses for testing purposes.

    ABBREV_PROB = {"blank": 0.50, "abbrev": 0.50}
    SUFFIX_PROB = {"blank": 0.50, "suffix": 0.50}
    INTERNAL_PROB = {"blank": 0.50, "internal": 0.50}
    ZIP4_PROB = {"blank": 0.50, "zip4": 0.50}

    # The number of instances to create for the test suite.
    N_INSTANCES = 100

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    @classmethod
    def setUpTestData(cls):
        """
        Set up the test environment before each test method is executed.
        """
        cls.address_list = Address.objects.bulk_create(
            [cls.create_fake_address() for _ in range(cls.N_INSTANCES)]
        )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    @classmethod
    def create_fake_address(cls):
        """
        Create a fake address for testing purposes.
        """

        # Define state here so we can use it in the zip code generation.
        stateabbrev = fake.state_abbr(
            include_territories=False, include_freely_associated_states=False
        )

        return Address(
            address_alphanumeric=fake.building_number(),
            predirabbrev=fake.random_element(
                elements=OrderedDict(
                    [
                        (
                            fake.random_element(Address.direction_abbreviations),
                            cls.ABBREV_PROB["abbrev"],
                        ),
                        ("", cls.ABBREV_PROB["blank"]),
                    ]
                )
            ),
            # This sometimes contains its own type, so we split it to get the street name.
            streetname=fake.street_name().split()[0],
            streettypeabbrev=fake.random_element(
                elements=OrderedDict(
                    [
                        (fake.street_suffix(), cls.SUFFIX_PROB["suffix"]),
                        ("", cls.SUFFIX_PROB["blank"]),
                    ]
                ),
            ),
            postdirabbrev=fake.random_element(
                elements=OrderedDict(
                    [
                        (
                            fake.random_element(Address.direction_abbreviations),
                            cls.ABBREV_PROB["abbrev"],
                        ),
                        ("", cls.ABBREV_PROB["blank"]),
                    ]
                )
            ),
            internal=fake.random_element(
                elements=OrderedDict(
                    [
                        (fake.secondary_address(), cls.INTERNAL_PROB["internal"]),
                        ("", cls.INTERNAL_PROB["blank"]),
                    ]
                ),
            ),
            location=fake.city(),
            stateabbrev=stateabbrev,
            zip=fake.zipcode_in_state(state_abbr=stateabbrev),
            zip4=fake.random_element(
                elements=OrderedDict(
                    [
                        (fake.zipcode_plus4().split("-")[1], cls.ZIP4_PROB["zip4"]),
                        ("", cls.ZIP4_PROB["blank"]),
                    ]
                ),
            ),
        )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    @classmethod
    def generate_symbols(cls, length):
        symbols = string.punctuation
        return "".join(fake.random.choice(symbols) for _ in range(length))

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_string_representation(self):
        """
        Test the string representation of the Address model.
        """
        for address in self.address_list:

            expected_string = " ".join(
                [
                    value
                    for value in [
                        address.address_alphanumeric,
                        address.predirabbrev,
                        address.streetname,
                        address.streettypeabbrev,
                        address.postdirabbrev,
                        address.internal,
                        address.location,
                        address.stateabbrev,
                        address.zip,
                        address.zip4,
                    ]
                    if value != ""
                ]
            )

            self.assertEqual(
                first=address.__str__(),
                second=expected_string,
                msg=f"Error occurred: The string representation of address with id '{address.id}' is incorrect: {address.__str__()} != {expected_string}",
            )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_creation(self):
        """
        Test the creation of an Address instance.
        """

        # Make we have the correct number of instances in the database.
        self.assertEqual(
            first=self.N_INSTANCES,
            second=Address.objects.count(),
            msg=f"Error occurred: Expected {self.N_INSTANCES} instances.",
        )

        for address in self.address_list:

            # Get the address from the database.
            db_addr = Address.objects.get(id=address.id)

            # Check that the fields of the local Address instance match the fields in the database.
            for field_name in Address.address_fields:

                self.assertEqual(
                    first=getattr(address, field_name),
                    second=getattr(db_addr, field_name),
                    msg=f"Error occurred: {field_name} fields do not match {address} != {db_addr}.",
                )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_required_fields(self):
        """
        Test that all required fields are indeed required.
        """

        for address in self.address_list:
            # Check that the required fields are required.
            for field_name in Address.required_fields:

                # Set the required field to an empty string to simulate a missing value.
                setattr(address, field_name, "")

                with self.assertRaises(
                    expected_exception=ValidationError,
                    msg=f"Error occurred: {field_name} field is required and should not be allowed to be blank. {address}",
                ):
                    address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_optional_fields(self):
        """
        Test that all optional fields are indeed optional.
        """

        for address in self.address_list:
            # Check that the optional fields are optional.
            for field_name in Address.optional_fields:

                # Set the optional field to an empty string to simulate a missing value.
                setattr(address, field_name, "")

                try:
                    address.full_clean()
                except ValidationError:
                    self.fail(
                        f"Error occurred: {field_name} field is optional and should be allowed to be blank."
                    )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_unique_constraint(self):
        """
        Test that the unique constraint is enforced.
        """
        for address in self.address_list:
            # Set pk to None and _state.adding to True to simulate a new instance.
            address.pk = None
            address._state.adding = True

            # Try to validate the duplicate address.
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: Duplicate address {address} should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_alphanumeric_address_field(self):
        """
        Test the alphanumeric address field validation.
        """
        for address in self.address_list:

            # A malformed address_alphanumeric field.
            address.address_alphanumeric = self.generate_symbols(16)

            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: address_alphanumeric {address.address_alphanumeric} is malformed and should not be allowed.",
            ):
                address.full_clean()

            # Test a too long address_alphanumeric field.

            address.address_alphanumeric = fake.pystr_format(
                string_format="################?"
            )

            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: address_alphanumeric {address.address_alphanumeric} is too long and should not be allowed.",
            ):
                address.full_clean()

            # Test a blank address_alphanumeric field.

            address.address_alphanumeric = ""
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: A blank address_alphanumeric should not be allowed, but was.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_predirabbrev_field(self):
        """
        Test the predirabbrev field validation.
        """
        for address in self.address_list:

            # A too long predirabbrev field.
            address.predirabbrev = fake.pystr(min_chars=3, max_chars=4)

            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: predirabbrev {address.predirabbrev} is too long and should not be allowed.",
            ):
                address.full_clean()

            try:
                # A blank predirabbrev field.
                address.predirabbrev = ""
                address.full_clean()

            except:
                self.fail(
                    f"Error occurred: A blank predirabbrev should be allowed, but was not."
                )

            # A malformed predirabbrev field.
            address.predirabbrev = self.generate_symbols(2)

            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: predirabbrev {address.predirabbrev} is malformed and should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_streetname_field(self):
        """
        Test the streetname field validation.
        """
        for address in self.address_list:
            # A blank streetname.
            address.streetname = ""
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: A blank streetname should not be allowed, but was.",
            ):
                address.full_clean()

            # A too long streetname.
            address.streetname = fake.pystr(min_chars=33, max_chars=34)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: streetname {address.streetname} is too long and should not be allowed.",
            ):
                address.full_clean()

            # Try a malformed streetname.
            address.streetname = self.generate_symbols(16)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: streetname {address.streetname} is malformed and should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_streettypeabbrev_field(self):
        """
        Test the streettypeabbrev field validation.
        """
        for address in self.address_list:

            # A malformed streettypeabbrev.
            address.streettypeabbrev = self.generate_symbols(8)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: streettypeabbrev {address.streettypeabbrev} is malformed and should not be allowed.",
            ):
                address.full_clean()

            try:
                # A blank streettypeabbrev.
                address.streettypeabbrev = ""
                address.full_clean()
            except ValidationError:
                self.fail(
                    f"Error occurred: A blank streettypeabbrev should be allowed, but was not."
                )

            # A too long streettypeabbrev.
            address.streettypeabbrev = fake.pystr(min_chars=17, max_chars=18)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: streettypeabbrev {address.streettypeabbrev} is too long and should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_postdirabbrev_field(self):
        """
        Test the postdirabbrev field validation.
        """
        for address in self.address_list:

            # A too long postdirabbrev.
            address.postdirabbrev = fake.pystr(min_chars=3, max_chars=4)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: postdirabbrev {address.postdirabbrev} is too long and should not be allowed.",
            ):
                address.full_clean()

            # A malformed postdirabbrev.
            address.postdirabbrev = self.generate_symbols(2)
            with self.assertRaises(
                expected_exception=ValidationError,
                msg="Error occurred: postdirabbrev is malformed and should not be allowed.",
            ):
                address.full_clean()

            try:
                # A blank postdirabbrev.
                address.postdirabbrev = ""
                address.full_clean()
            except ValidationError:
                self.fail(
                    f"Error occurred: A blank postdirabbrev should be allowed, but was not."
                )

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************
    def test_address_internal_field(self):
        """
        Test that the internal field is validated.
        """
        for address in self.address_list:

            # A too long internal field.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: internal {address.internal} is too long and should not be allowed.",
            ):
                address.internal = fake.pystr(min_chars=33, max_chars=34)
                address.full_clean()

            # A malformed internal field.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: internal {address.internal} is malformed and should not be allowed.",
            ):
                address.internal = self.generate_symbols(16)
                address.full_clean()

            # A blank internal field should be allowed.
            # Here, we test that setting it to blank does not raise a ValidationError.
            try:
                address.internal = ""
                address.full_clean()  # This should not raise an error
            except ValidationError:
                self.fail("Error occurred: A blank internal field should be allowed.")

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_location_field(self):
        """
        Test that the location field is validated.
        """
        for address in self.address_list:

            # A blank location field.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: A blank location should not be allowed, but was.",
            ):
                address.location = ""
                address.full_clean()

            # A malformed location field.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: location {address.location} is malformed and should not be allowed.",
            ):
                address.location = self.generate_symbols(16)
                address.full_clean()

            # A too long location field.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: location {address.location} is too long and should not be allowed.",
            ):
                address.location = fake.pystr(min_chars=33, max_chars=34)
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_stateabbrev_field(self):
        """
        Test that the stateabbrev field is validated.
        """
        for address in self.address_list:

            # A too long stateabbrev.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occurred: stateabbrev {address.stateabbrev} is too long and should not be allowed.",
            ):
                address.stateabbrev = fake.pystr_format(string_format="???")
                address.full_clean()

            # A blank stateabbrev.
            with self.assertRaises(
                ValidationError,
                msg="Error occurred: A blank stateabbrev should not be allowed, but was.",
            ):
                address.stateabbrev = ""
                address.full_clean()

            # A malformed stateabbrev.
            with self.assertRaises(
                ValidationError,
                msg=f"Error occured: stateabbrev {address.stateabbrev} is malformed and should not be allowed.",
            ):
                address.stateabbrev = self.generate_symbols(2)
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_zip_field(self):
        """
        Test that the zip field is validated.
        """
        for address in self.address_list:

            # A malformed zip field.
            address.zip = fake.pystr_format(string_format="?????")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip {address.zip} is malformed and should not be allowed.",
            ):
                address.full_clean()

            # A blank zip field.
            address.zip = ""
            with self.assertRaises(
                expected_exception=ValidationError,
                msg="A blank zip should not be allowed, but was.",
            ):
                address.full_clean()

            # A too long zip field.
            address.zip = fake.pystr_format(string_format="######")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip {address.zip} is too long and should not be allowed.",
            ):
                address.full_clean()

            # A too short zip field.
            address.zip = fake.pystr_format(string_format="###")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip {address.zip} is too short and should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_zip4_field_validation(self):
        """
        Test that the zip4 field is validated.
        """
        for address in self.address_list:

            # A malformed zip4 field.
            address.zip4 = fake.pystr_format(string_format="????")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip4 {address.zip4} is malformed and should not be allowed.",
            ):
                address.full_clean()

            # A too long zip4 field.
            address.zip4 = fake.pystr_format(string_format="#####")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip4 {address.zip4} is too long and should not be allowed.",
            ):
                address.full_clean()

            try:
                # A blank zip4 field.
                address.zip4 = ""
                address.full_clean()
            except ValidationError:
                self.fail(
                    f"Error occurred: A blank zip4 should be allowed, but was not."
                )

            # A too short zip4 field.
            address.zip4 = fake.pystr_format(string_format="##")
            with self.assertRaises(
                expected_exception=ValidationError,
                msg=f"Error occurred: zip4 {address.zip4} is too short and should not be allowed.",
            ):
                address.full_clean()

    # **********************************************************************************************************************
    # **********************************************************************************************************************
    # **********************************************************************************************************************

    def test_address_deletion(self):
        """
        Test the deletion of database Address instances.
        """
        # Check that the Address instances exist in the database.
        self.assertEqual(
            first=self.N_INSTANCES,
            second=Address.objects.count(),
            msg=f"Error occurred: Expected {self.N_INSTANCES} instances.",
        )

        # Delete the instances from the locally created list from the database.
        Address.objects.all().delete()

        # Check that the Address instances have been deleted from the database.
        self.assertEqual(
            first=Address.objects.count(),
            second=0,
            msg="Error occurred: Expected 0 instances.",
        )
