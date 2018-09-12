"""
Cloudless command line entry point.
"""
from cloudless.cli.cldls import get_cldls

def main():
    """
    Main entry point.
    """
    cldls_cli = get_cldls()
    # pylint: disable=no-value-for-parameter
    cldls_cli()

if __name__ == '__main__':
    main()
