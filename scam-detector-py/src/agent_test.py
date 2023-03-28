from forta_agent import create_alert_event,FindingSeverity, AlertEvent, Label, EntityType
import agent
import json
import pandas as pd
import numpy as np
from datetime import datetime
from web3_mock import Web3Mock, EOA_ADDRESS_2, EOA_ADDRESS, CONTRACT
from constants import MODEL_ALERT_THRESHOLD_LOOSE, MODEL_ALERT_THRESHOLD_STRICT

w3 = Web3Mock()


class TestScamDetector:
    def generate_alert(address: str, bot_id: str, alert_id: str, timestamp: int, metadata={}, labels=[]) -> AlertEvent:
        # {
        #       "label": "Attacker",
        #       "confidence": 0.25,
        #       "entity": "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820",
        #       "entityType": "ADDRESS",
        #       "remove": false
        # },

        if len(labels)>0:
            alert = {"alert":
                    {"name": "x",
                    "hash": "0xabc",
                    "addresses": [],
                    "description": f"{address} description",
                    "alertId": alert_id,
                    "createdAt": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S.%f123Z"),  # 2022-11-18T03:01:21.457234676Z
                    "source":
                        {"bot": {'id': bot_id}, "block": {"chainId": 1, 'number': 5},  'transactionHash': '0x123'},
                    "metadata": metadata,
                    "labels": labels
                    }
                    }
        else:
            addresses = [address] 
            alert = {"alert":
                    {"name": "x",
                    "hash": "0xabc",
                    "addresses": addresses,
                    "description": f"{address} description",
                    "alertId": alert_id,
                    "createdAt": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S.%f123Z"),  # 2022-11-18T03:01:21.457234676Z
                    "source":
                        {"bot": {'id': bot_id}, "block": {"chainId": 1, 'number': 5}, 'transactionHash': '0x123'},
                    "metadata": metadata,
                   
                    }
                    }
        return create_alert_event(alert)
    
    def test_is_contract(self):
        assert agent.is_contract(w3, EOA_ADDRESS) == False, "should be false"
        assert agent.is_contract(w3, CONTRACT) == True, "should be false"
        
    
    def test_initialize(self):
        subscription_json = agent.initialize()
        json.dumps(subscription_json)
        assert True, "Bot should initialize successfully"

    def test_in_list(self):
        agent.initialize()
        alert = create_alert_event(
            {"alert":
                {"name": "x",
                 "hash": "0xabc",
                 "description": "description",
                 "alertId": "SUSPICIOUS-CONTRACT-CREATION",
                 "source":
                    {"bot": {'id': "0x457aa09ca38d60410c8ffa1761f535f23959195a56c9b82e0207801e86b34d99"}}
                 }
             })

        assert agent.in_list(alert, agent.BASE_BOTS), "should be in list"

    def test_in_list_incorrect_alert_id(self):
        agent.initialize()
        alert = create_alert_event(
            {"alert":
                {"name": "x",
                 "hash": "0xabc",
                 "description": "description",
                 "alertId": "ICE-PHISHING-ERC20-APPROVAL-FOR-ALL-INCORRECT",
                 "source":
                    {"bot": {'id': "0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14"}}
                 }
             })

        assert not agent.in_list(alert, agent.BASE_BOTS), "should be in list"

    def test_in_list_incorrect_bot_id(self):
        agent.initialize()
        alert = create_alert_event(
            {"alert":
                {"name": "x",
                 "hash": "0xabc",
                 "description": "description",
                 "alertId": "ICE-PHISHING-ERC20-APPROVAL-FOR-ALL",
                 "source":
                    {"bot": {'id': "0xe8527df509859e531e58ba4154e9157eb6d9b2da202516a66ab120deabdaaaaa"}}
                 }
             })

        assert not agent.in_list(alert, agent.BASE_BOTS), "should be in list"

    def test_get_etherscan_label_has_label(self):
        label = agent.get_etherscan_label("0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc")
        assert "tornado" in label, "should be sanctioned label"

    def test_get_etherscan_label_no_label(self):
        label = agent.get_etherscan_label("0xa0109274F53609f6Be97ec5f3052C659AB80f012")
        assert label == None, "should be no label"

    def test_get_shard(self):
        package_json = json.load(open("package.json"))
        chain_id = 1
        total_chards = package_json["chainSettings"][str(chain_id)]["shards"]

        assert total_chards == 3

        for block_number in range(1, total_chards):
            shard = agent.get_shard(block_number)
            assert shard == block_number, "should be " + str(block_number)

        shard = agent.get_shard(total_chards)
        assert shard == 0, "should be 0"

    def test_put_alert(self):
        agent.initialize()
       
        timestamp = 1679508064
        alert = TestScamDetector.generate_alert(EOA_ADDRESS, "0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-4", timestamp)
        agent.put_alert(alert, EOA_ADDRESS)
        agent.put_alert(alert, EOA_ADDRESS)

        alerts = agent.read_alerts(EOA_ADDRESS)
        assert len(alerts) == 1, "should be 1 alert"
        assert ("0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-4", "0xabc") in alerts, "should be in alerts"

    def test_put_alert_multiple_shards(self):
        agent.initialize()

        timestamp_1 = 1679508064
        shard1 = agent.get_shard(timestamp_1)

        timestamp_2 = timestamp_1 + 1
        shard2 = agent.get_shard(timestamp_2)
        assert shard1 != shard2, "should be different shards"

        alert = TestScamDetector.generate_alert(EOA_ADDRESS_2, "0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-1", timestamp_1)
        agent.put_alert(alert, EOA_ADDRESS_2)

        alert = TestScamDetector.generate_alert(EOA_ADDRESS_2, "0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-2", timestamp_2)
        agent.put_alert(alert, EOA_ADDRESS_2)

        alerts = agent.read_alerts(EOA_ADDRESS_2)
        assert len(alerts) == 2, "should be 2 alert"
        assert ("0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-1", "0xabc") in alerts, "should be in alerts"
        assert ("0xa91a31df513afff32b9d85a2c2b7e786fdd681b3cdd8d93d6074943ba31ae400", "FUNDING-TORNADO-CASH-2", "0xabc") in alerts, "should be in alerts"

    def test_build_feature_vector(self):
        # alerts are tuples of (botId, alertId, alertHash)
        alerts = [('0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5', 'FLASHBOTS-TRANSACTIONS', '0x1'),
                  ('0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14', 'ICE-PHISHING-ERC20-PERMIT', '0x2'),
                  ('0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14', 'ICE-PHISHING-ERC721-APPROVAL-FOR-ALL', '0x3'),
                  ('0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14', 'ICE-PHISHING-ERC721-APPROVAL-FOR-ALL', '0x4')
                  ]

        df_expected_feature_vector = pd.DataFrame(columns=agent.MODEL_FEATURES)
        df_expected_feature_vector.loc[0] = np.zeros(len(agent.MODEL_FEATURES))
        df_expected_feature_vector.iloc[0]["0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5_FLASHBOTS-TRANSACTIONS"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_ICE-PHISHING-ERC20-PERMIT"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_ICE-PHISHING-ERC721-APPROVAL-FOR-ALL"] = 2
        df_expected_feature_vector.iloc[0]["0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5_count"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_count"] = 3

        df_feature_vector = agent.build_feature_vector(alerts, EOA_ADDRESS)
        assert df_feature_vector.equals(df_expected_feature_vector), "should be equal"

    def test_get_score(self):
        agent.initialize()

        df_expected_feature_vector = pd.DataFrame(columns=agent.MODEL_FEATURES)
        df_expected_feature_vector.loc[0] = np.zeros(len(agent.MODEL_FEATURES))
        df_expected_feature_vector.iloc[0]["0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5_FLASHBOTS-TRANSACTIONS"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_ICE-PHISHING-ERC20-PERMIT"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_ICE-PHISHING-ERC721-APPROVAL-FOR-ALL"] = 2
        df_expected_feature_vector.iloc[0]["0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5_count"] = 1
        df_expected_feature_vector.iloc[0]["0x8badbf2ad65abc3df5b1d9cc388e419d9255ef999fb69aac6bf395646cf01c14_count"] = 3

        score = agent.get_model_score(df_expected_feature_vector)
        assert score > MODEL_ALERT_THRESHOLD_LOOSE, "should greater than model threshold"

    def test_get_score_empty_features(self):
        agent.initialize()

        df_expected_feature_vector = pd.DataFrame(columns=agent.MODEL_FEATURES)
        df_expected_feature_vector.loc[0] = np.zeros(len(agent.MODEL_FEATURES))
        

        score = agent.get_model_score(df_expected_feature_vector)
        assert score < MODEL_ALERT_THRESHOLD_LOOSE, "should less than model threshold"


    def test_scam(self):
        agent.initialize()

        label = Label({
                'entityType': EntityType.Address,
                'label': "scammer",
                'entity': EOA_ADDRESS,
                'confidence': 1.0,
                'remove': "false"
                })

        timestamp = datetime.now().timestamp()
        alert1 = TestScamDetector.generate_alert(EOA_ADDRESS, "0xbc06a40c341aa1acc139c900fd1b7e3999d71b80c13a9dd50a369d8f923757f5","FLASHBOTS-TRANSACTIONS", timestamp, {}, [label])
        findings = agent.detect_scam(w3, alert1)
        assert len(findings) == 0, "should be 0 finding"

        