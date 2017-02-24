"""Runs the digital comms model within the NISMOD v2.0 system of systems model
"""

from smif.sector_model import SectorModel 
from digital_comms.fixed import run

class DigitalCommsWrapper(SectorModel):

    def extract_obj():
        pass

    def simulate(self, decisions, state, data):
        """Runs the digital comms model

        Arguments
        ---------
        decisions: list
            A list of decisions from the integration framework
        state: list
            Not yet implemented
        data: list
            The data received from the integration framework

        Returns
        -------
        results: dict
            A nested dict containing the model results

        Notes
        -----

        decisions are in the format::

                [{name: G.fast_geo1
                    capital_cost:
                        value: 2201
                        units: £(million)
                    economic_lifetime:
                        value: 15
                        units: years
                    operational_life:
                        value: 15
                        units: years
                    capacity:
                        value: 2000
                        units: Mbps
                    location: Great Britain}]

        """
        # Run the model

        results = run(decisions, '/vagrant/models/digital_comms/data/exchanges.csv')
        return results

if __name__ == '__main__':

    decisions = []
    digi = DigitalCommsWrapper()
    print(digi.simulate(decisions, [], {}))
