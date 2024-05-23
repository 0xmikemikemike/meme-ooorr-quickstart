import {
  CopyOutlined,
  InfoCircleOutlined,
  // QrcodeOutlined
} from '@ant-design/icons';
import {
  Alert,
  Button,
  Flex,
  message,
  // Popover,
  // QRCode,
  Tooltip,
  Typography,
} from 'antd';
import { useEffect, useMemo } from 'react';
import styled from 'styled-components';

import { Chain } from '@/client';
import { copyToClipboard } from '@/common-util';
import { CardFlex } from '@/components/styled/CardFlex';
import { CardSection } from '@/components/styled/CardSection';
import {
  COLOR,
  COW_SWAP_GNOSIS_XDAI_OLAS_URL,
  MIN_ETH_BALANCE_THRESHOLDS,
} from '@/constants';
import { UNICODE_SYMBOLS } from '@/constants/unicode';
import { SetupScreen } from '@/enums';
import { useBalance, useSetup } from '@/hooks';
import { useWallet } from '@/hooks/useWallet';
import { Address } from '@/types';

import { SetupCreateHeader } from './SetupCreateHeader';

export const SetupEoaFunding = () => {
  const { masterEoaAddress } = useWallet();
  const { walletBalances } = useBalance();
  const { goto } = useSetup();

  const masterEaoEthBalance =
    masterEoaAddress && walletBalances?.[masterEoaAddress]?.ETH;

  const isFundedMasterEoa =
    masterEaoEthBalance &&
    masterEaoEthBalance >=
      MIN_ETH_BALANCE_THRESHOLDS[Chain.GNOSIS].safeCreation;

  const statusMessage = useMemo(() => {
    if (!isFundedMasterEoa) {
      return 'Waiting for transaction';
    } else {
      return 'Funds have been received!';
    }
  }, [isFundedMasterEoa]);

  useEffect(() => {
    // Move to create the safe stage once the master EOA is funded
    if (!isFundedMasterEoa) return;
    message.success('Funds have been received!');
    goto(SetupScreen.SetupCreateSafe);
  }, [goto, isFundedMasterEoa]);

  return (
    <CardFlex>
      <SetupCreateHeader prev={SetupScreen.SetupBackupSigner} />
      <Typography.Title level={3}>
        Deposit {MIN_ETH_BALANCE_THRESHOLDS[Chain.GNOSIS].safeCreation} XDAI on
        Gnosis
      </Typography.Title>
      <Typography.Paragraph>
        The app needs these funds to create your account on-chain.
      </Typography.Paragraph>

      <CardSection bordertop="true" borderbottom="true">
        <Typography.Text
          className={!isFundedMasterEoa ? 'loading-ellipses' : ''}
        >
          Status: {statusMessage}
        </Typography.Text>
      </CardSection>
      {!isFundedMasterEoa && (
        <SetupEoaFundingWaiting masterEoa={masterEoaAddress} />
      )}
    </CardFlex>
  );
};

const SetupEoaFundingWaiting = ({
  masterEoa,
}: {
  masterEoa: Address | undefined;
}) => {
  return (
    <>
      <CardSection>
        <Alert
          className="card-section-alert"
          type="warning"
          showIcon
          message={
            <Flex vertical gap={5}>
              <Typography.Text strong style={{ color: COLOR.BROWN }}>
                Only send funds on Gnosis Chain!
              </Typography.Text>
              <Typography.Text style={{ color: COLOR.BROWN }}>
                You will lose any assets you send on other chains.
              </Typography.Text>
            </Flex>
          }
        />
      </CardSection>
      <AccountCreationCard>
        <Flex justify="space-between">
          <Typography.Text className="text-sm" type="secondary">
            Account creation address
          </Typography.Text>
          <Flex gap={10} align="center">
            <Tooltip title="Copy to clipboard">
              <CopyOutlined
                style={ICON_STYLE}
                onClick={() =>
                  masterEoa &&
                  copyToClipboard(masterEoa).then(() =>
                    message.success('Address copied!'),
                  )
                }
              />
            </Tooltip>

            {/* {masterEoa && (
                <Popover
                  title="Scan QR code"
                  content={
                    <QRCode
                      size={250}
                      value={`https://metamask.app.link/send/${masterEoa}@${100}`}
                    />
                  }
                >
                  <QrcodeOutlined style={ICON_STYLE}/>
                </Popover>
              )} */}
          </Flex>
        </Flex>

        <span className="can-select-text break-word">
          {`GNO: ${masterEoa}`}
        </span>
        <Alert
          className="account-creation-alert"
          showIcon
          icon={<InfoCircleOutlined />}
          message={
            'After this point, do not send more funds to this address. Once your account is created, you will be given a new address - send further funds there.'
          }
        />
      </AccountCreationCard>
      <Button type="link" target="_blank" href={COW_SWAP_GNOSIS_XDAI_OLAS_URL}>
        Get XDAI on Gnosis Chain {UNICODE_SYMBOLS.EXTERNAL_LINK}
      </Button>
    </>
  );
};

const AccountCreationCard = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background-image: url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='12' ry='12' stroke='%23A3AEBB' stroke-width='2' stroke-dasharray='6' stroke-dashoffset='15' stroke-linecap='square'/%3e%3c/svg%3e");
  border-radius: 12px;

  .account-creation-alert {
    margin-top: 8px;
    background: #e6f4ff;
    border: 1px solid #91caff;
    color: #002c8c;
    align-items: flex-start;
  }
`;

const ICON_STYLE = { color: '#606F85' };
