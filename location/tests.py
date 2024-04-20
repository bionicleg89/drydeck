import logging
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

    # The number of iterations to run the test methods.
    ITERATIONS = 100

    @classmethod
    def setUpTestData(cls):
        """
        Set up the test data for the Address model.
        """
        cls.address = Address()
        cls.duplicate_address = Address()

    @classmethod
    def create_fake_address(cls):
        """
        Create a fake address for testing purposes.
        """
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

    def test_address_string_representation(self):
        """
        Test the string representation of the Address model.
        """
        for _ in range(self.ITERATIONS):

            self.address = self.create_fake_address()
            self.address.full_clean()
            self.address.save()

            try:
                expected_string = " ".join(
                    [
                        f"{value}"
                        for value in [
                            self.address.address_alphanumeric,
                            self.address.predirabbrev,
                            self.address.streetname,
                            self.address.streettypeabbrev,
                            self.address.postdirabbrev,
                            self.address.internal,
                            self.address.location,
                            self.address.stateabbrev,
                            self.address.zip,
                            self.address.zip4,
                        ]
                        if value != ""
                    ]
                )

                self.assertEqual(str(self.address), expected_string)
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

            # Now confirm it throws an error if the strings don't match.
            try:
                self.assertNotEqual(
                    str(self.address), " ".join([fake.word() for _ in range(10)])
                )

                self.assertEqual(str(self.address), expected_string)
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_creation(self):
        """
        Test the creation of an Address instance.
        """
        for _ in range(1, self.ITERATIONS + 1):
            try:
                self.address = self.create_fake_address()
                self.address.full_clean()
                self.address.save()

                self.assertEqual(Address.objects.count(), _)
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

            try:
                address_from_db = Address.objects.get(pk=self.address.pk)
                self.assertEqual(self.address, address_from_db)
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_required_fields(self):
        """
        Test that all required fields are indeed required.
        """
        for _ in range(self.ITERATIONS):
            try:
                self.address = self.create_fake_address()
                required_fields = Address.required_fields
                for field in required_fields:
                    setattr(self.address, field.name, None)
                    with self.assertRaises(ValidationError):
                        self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_unique_constraint(self):
        """
        Test that the unique constraint is enforced.
        """
        for _ in range(self.ITERATIONS):
            try:
                self.address = self.create_fake_address()
                self.address.full_clean()
                self.address.save()

                # Set pk to None and _state.adding to True to simulate a new instance.
                self.address.pk = None
                self.address._state.adding = True

                with self.assertRaises(ValidationError):
                    self.address.full_clean()

            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_alnum_address_field(self):
        """
        Test the alphanumeric address field validation.
        """
        for _ in range(self.ITERATIONS):
            self.address = self.create_fake_address()

            try:
                self.address.address_alphanumeric = fake.password(length=10)
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

            try:
                self.address.address_alphanumeric = "".join(
                    [
                        self.address.address_alphanumeric,
                        fake.building_number(),
                    ]
                )
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_predirabbrev_field(self):
        """
        Test the predirabbrev field validation.
        """
        for _ in range(self.ITERATIONS):
            self.address = self.create_fake_address()

            try:
                self.address.predirabbrev = fake.word()
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_streetname_field(self):
        """
        Test the streetname field validation.
        """
        for _ in range(self.ITERATIONS):
            self.address = self.create_fake_address()

            try:
                self.address.streetname = ""
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

            try:
                self.address.streetname = fake.sentence(nb_words=10)
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_streettypeabbrev_field(self):
        """
        Test the streettypeabbrev field validation.
        """
        for _ in range(self.ITERATIONS):
            self.address = self.create_fake_address()

            try:
                self.address.streettypeabbrev = fake.sentence(nb_words=10)
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}\n{self.address.streettypeabbrev}")
                raise e

    def test_address_postdirabbrev_field(self):
        """
        Test the postdirabbrev field validation.
        """
        for _ in range(self.ITERATIONS):
            self.address = self.create_fake_address()

            try:
                self.address.postdirabbrev = fake.word()
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_internal_field(self):
        """
        Test that the internal field is validated.
        """
        for _ in range(self.ITERATIONS):
            # Create address.
            self.address = self.create_fake_address()

            # Test length validation.
            try:
                self.address.internal = fake.sentence(nb_words=10)

                with self.assertRaises(ValidationError):
                    self.address.full_clean()

            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_location_field(self):
        """
        Test that the location field is validated.
        """
        for _ in range(self.ITERATIONS):
            # Create address.
            self.address = self.create_fake_address()

            # Test blank validation.
            try:
                self.address.location = ""
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_stateabbrev_field(self):
        """
        Test that the stateabbrev field is validated.
        """
        for _ in range(self.ITERATIONS):
            # Create address.
            self.address = self.create_fake_address()

            # Test regex validation.
            try:
                self.address.stateabbrev = fake.word() + fake.word()
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}\n{self.address.stateabbrev}")
                raise e

    def test_address_zip_field(self):
        """
        Test that the zip field is validated.
        """
        for _ in range(self.ITERATIONS):
            # Create address.
            self.address = self.create_fake_address()

            # Test regex validation.
            try:
                self.address.zip = fake.word()
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e

    def test_address_zip4_field(self):
        """
        Test that the zip4 field is validated.
        """
        for _ in range(self.ITERATIONS):
            # Create address.
            self.address = self.create_fake_address()

            # Test regex validation.
            try:
                self.address.zip4 = fake.word()
                with self.assertRaises(ValidationError):
                    self.address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                raise e
