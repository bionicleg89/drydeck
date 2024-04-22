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

    # The number of instances to create for each test method.
    N_INSTANCES = 100

    def setUp(self):
        """
        Set up the test environment before each test method is executed.
        """
        self.address_list = []

        # Create N_INSTANCES of Address objects for testing.
        for _ in range(self.N_INSTANCES):
            address = self.create_fake_address()
            self.address_list.append(address)
            address.save()

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
        for address in self.address_list:
            try:
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

                self.assertEqual(address.__str__(), expected_string)

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

            # Now confirm it throws an error if the strings don't match.
            try:
                self.assertNotEqual(
                    address.__str__(), " ".join([fake.word() for _ in range(10)])
                )

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_creation(self):
        """
        Test the creation of an Address instance.
        """
        for local_addr, db_addr in zip(
            sorted(self.address_list, key=lambda x: x.id),
            Address.objects.all().order_by("id"),
        ):
            try:
                for field_name in Address.address_fields:
                    self.assertEqual(
                        getattr(local_addr, field_name),
                        getattr(db_addr, field_name),
                    )
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_required_fields(self):
        """
        Test that all required fields are indeed required.
        """

        for address in self.address_list:
            try:
                for field in Address.required_fields:
                    setattr(address, field.name, None)

                    with self.assertRaises(ValidationError):
                        address.full_clean()
                        address.save()

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_unique_constraint(self):
        """
        Test that the unique constraint is enforced.
        """
        for address in self.address_list:
            try:
                address.full_clean()
                address.save()

                # Set pk to None and _state.adding to True to simulate a new instance.
                address.pk = None
                address._state.adding = True

                # Try to save the same address again.
                with self.assertRaises(ValidationError):
                    address.full_clean()
                    address.save()

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

            # Check that the constraint does not apply to a slightly different address.
            try:
                address.address_alphanumeric = fake.building_number()

                # Check it does not raise a validation error.
                address.full_clean()
                address.save()

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_alphanumeric_address_field_validation(self):
        """
        Test the alphanumeric address field validation.
        """
        for address in self.address_list:
            # Test a malformed address_alphanumeric field.
            try:
                address.address_alphanumeric = fake.password(length=10)

                with self.assertRaises(ValidationError):
                    address.full_clean()
                    address.save()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e
            # Test a too long address_alphanumeric field.
            try:
                address.address_alphanumeric = "".join([fake.word() for _ in range(10)])

                with self.assertRaises(ValidationError):
                    address.full_clean()
                    address.save()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_predirabbrev_field(self):
        """
        Test the predirabbrev field validation.
        """
        for address in self.address_list:
            try:
                address.predirabbrev = fake.word()
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_streetname_field(self):
        """
        Test the streetname field validation.
        """
        for address in self.address_list:
            try:
                address.streetname = ""
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

            try:
                address.streetname = fake.sentence(nb_words=10)
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_streettypeabbrev_field(self):
        """
        Test the streettypeabbrev field validation.
        """
        for address in self.address_list:
            try:
                address.streettypeabbrev = fake.sentence(nb_words=10)
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_postdirabbrev_field(self):
        """
        Test the postdirabbrev field validation.
        """
        for address in self.address_list:
            try:
                address.postdirabbrev = fake.word()
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_internal_field(self):
        """
        Test that the internal field is validated.
        """
        for address in self.address_list:
            try:
                address.internal = fake.sentence(nb_words=10)

                with self.assertRaises(ValidationError):
                    address.full_clean()

            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_location_field(self):
        """
        Test that the location field is validated.
        """
        for address in self.address_list:
            try:
                address.location = ""
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_stateabbrev_field(self):
        """
        Test that the stateabbrev field is validated.
        """
        for address in self.address_list:
            try:
                address.stateabbrev = fake.word() + fake.word()
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_zip_field(self):
        """
        Test that the zip field is validated.
        """
        for address in self.address_list:
            try:
                address.zip = fake.word()
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_zip4_field_validation(self):
        """
        Test that the zip4 field is validated.
        """
        for address in self.address_list:
            try:
                address.zip4 = fake.word()
                with self.assertRaises(ValidationError):
                    address.full_clean()
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e

    def test_address_deletion(self):
        """
        Test the deletion of an Address instance.
        """

        for local_addr, db_addr in zip(
            sorted(self.address_list, key=lambda x: x.id),
            Address.objects.all().order_by("id"),
        ):
            try:
                db_addr.delete()
                # Check that the address has been deleted from the database.
                self.assertNotIn(local_addr, Address.objects.all())
            except Exception as e:
                logger.error(f"Error occurred: {e}", exc_info=True)
                raise e
