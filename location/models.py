from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.functional import classproperty


class Address(models.Model):
    """
    Represents an address with various components.

    Attributes:
        address_alphanumeric (str): The building number of the address.
            Example: '1234' or '1234A'.
        predirabbrev (str): The direction prefix of the street.
            Example: 'N' or 'NW'.
        streetname (str): The name of the street.
            Example: 'Main' or 'Elm'.
        streettypeabbrev (str): The type of the street.
            Example: 'St' or 'Ave'.
        postdirabbrev (str): The direction suffix of the street.
            Example: 'S' or 'SE'.
        internal (str): The internal address.
            Example: 'Apt 1' or 'Suite 100'.
        location (str): The city of the address.
            Example: 'Springfield' or 'Rivertown'.
        stateabbrev (str): The state of the address.
            Example: 'CA' or 'NY'.
        zip (str): The ZIP code of the address.
            Example: '12345'.
        zip4 (str): The ZIP+4 code of the address.
            Example: '6789'.

    Meta:
        constraints (list): A list of constraints for the model.
        verbose_name (str): The singular name of the model.
        verbose_name_plural (str): The plural name of the model.
        ordering (list): The default ordering of the model.

    Methods:
        __str__(): Returns a string representation of the address.
    """

    address_alphanumeric = models.CharField(
        verbose_name="Building Number",
        help_text="The building number of the address: e.g., '1234' or '1234A'.",
        max_length=16,
        blank=False,
        validators=[RegexValidator(r"^\d+[A-Z]?$", "Invalid house number.")],
    )

    predirabbrev = models.CharField(
        verbose_name="Direction Prefix",
        help_text="The direction prefix of the street: e.g., 'N' or 'NW'.",
        max_length=2,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[NS]?[EW]?$", "Invalid direction prefix.")],
    )

    streetname = models.CharField(
        verbose_name="Street Name",
        help_text="The name of the street: e.g., 'Main' or 'Elm'.",
        max_length=32,
        blank=False,
        validators=[RegexValidator(r"^[A-Za-z\s]+$", "Invalid street name.")],
    )

    streettypeabbrev = models.CharField(
        verbose_name="Street Type",
        help_text="The type of the street: e.g., 'St' or 'Ave'.",
        max_length=16,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[A-Za-z]+\.?$", "Invalid street type.")],
    )

    postdirabbrev = models.CharField(
        verbose_name="Direction Suffix",
        help_text="The direction suffix of the street: e.g., 'S' or 'SE'.",
        max_length=2,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[NS]?[EW]?$", "Invalid direction suffix.")],
    )

    internal = models.CharField(
        verbose_name="Internal",
        help_text="The internal address: e.g., 'Apt 1' or 'Suite 100'.",
        max_length=32,
        blank=True,
        default="",
        validators=[
            RegexValidator(r"^(?:[A-Za-z]+\.*\s\d+)$", "Invalid internal address.")
        ],
    )

    location = models.CharField(
        verbose_name="City",
        help_text="The city of the address: e.g., 'Springfield' or 'Rivertown'.",
        max_length=32,
        blank=False,
        validators=[RegexValidator(r"^[A-Za-z\s]+$", "Invalid city.")],
    )

    stateabbrev = models.CharField(
        verbose_name="State",
        help_text="The state of the address: e.g., 'CA' or 'NY'.",
        max_length=2,
        validators=[RegexValidator(r"^[A-Z]{2}$", "Invalid state.")],
        blank=False,
    )

    zip = models.CharField(
        verbose_name="ZIP Code",
        help_text="The ZIP code of the address: e.g., '12345'.",
        max_length=5,
        validators=[RegexValidator(r"^\d{5}$", "Invalid ZIP code.")],
        blank=False,
    )

    zip4 = models.CharField(
        verbose_name="ZIP+4 Code",
        help_text="The ZIP+4 code of the address: e.g., '6789'.",
        max_length=4,
        validators=[RegexValidator(r"^\d{4}$", "Invalid ZIP+4 code.")],
        blank=True,
        default="",
    )

    @classproperty
    def required_fields(cls):
        return (field for field in cls._meta.fields if not field.blank)

    @classproperty
    def direction_abbreviations(cls):
        """
        Returns a list of available direction abbreviations.
        """
        return ("N", "S", "E", "W", "NE", "NW", "SE", "SW")

    @classproperty
    def address_fields(cls):
        """
        Returns a list of address fields.
        """
        return [
            "address_alphanumeric",
            "predirabbrev",
            "streetname",
            "streettypeabbrev",
            "postdirabbrev",
            "internal",
            "location",
            "stateabbrev",
            "zip",
            "zip4",
        ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "address_alphanumeric",
                    "predirabbrev",
                    "streetname",
                    "streettypeabbrev",
                    "postdirabbrev",
                    "internal",
                    "location",
                    "stateabbrev",
                    "zip",
                    "zip4",
                ],
                name="unique_address",
                violation_error_message="The address already exists.",
            )
        ]
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = [
            "zip",
            "stateabbrev",
            "location",
            "streetname",
            "address_alphanumeric",
        ]

    def __str__(self):
        """
        Returns a string representation of the address.
        """
        val = " ".join(
            [
                getattr(self, field.name)
                for field in self._meta.fields
                if field.name != "id"
            ]
        )

        return " ".join(val.split())
