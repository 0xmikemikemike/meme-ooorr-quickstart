import {
  ArrowDownOutlined,
  CloseOutlined,
  CopyOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { Alert, Button, Flex, message, QRCode, Typography } from 'antd';
import { useCallback, useMemo } from 'react';

import { copyToClipboard, truncateAddress } from '@/common-util';
import { PageState } from '@/enums';
import { usePageState, useWallet } from '@/hooks';

import { Header } from '../Layout/Header';
import { Wrapper } from '../Layout/Wrapper';

export const Receive = () => {
  const { setPageState } = usePageState();
  const { wallets } = useWallet();

  const walletAddress = useMemo(() => wallets[0]?.address, [wallets]);
  const truncatedWalletAddress = useMemo(
    () => truncateAddress(walletAddress),
    [walletAddress],
  );

  const handleCopy = useCallback(
    () =>
      copyToClipboard(walletAddress).then(() =>
        message.success('Copied successfully!'),
      ),
    [walletAddress],
  );

  return (
    <>
      <Header>
        <ArrowDownOutlined />
        <Typography style={{ margin: 0 }}>Receive</Typography>
        <Button
          type="text"
          style={{ marginLeft: 'auto' }}
          onClick={() => setPageState(PageState.Main)}
        >
          <CloseOutlined />
        </Button>
      </Header>
      <Wrapper>
        <Flex vertical align="center" gap={20}>
          <Alert
            type="warning"
            icon={<WarningOutlined />}
            showIcon
            message={
              <Flex vertical gap={5}>
                <Typography.Text style={{ fontSize: 16 }} strong>
                  Only send assets on Gnosis Chain!
                </Typography.Text>
                <Typography.Text style={{ fontSize: 16 }}>
                  You will lose any assets you send on other chains
                </Typography.Text>
              </Flex>
            }
          />
          <QRCode
            value={`https://metamask.app.link/send/${walletAddress}@${100}`}
          />
          <Flex gap={10}>
            <Typography.Text
              className="can-select-text"
              code
              title={walletAddress}
            >
              {truncatedWalletAddress}
            </Typography.Text>
            <Button onClick={handleCopy}>
              <CopyOutlined />
            </Button>
          </Flex>
        </Flex>
      </Wrapper>
    </>
  );
};