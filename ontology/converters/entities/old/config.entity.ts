import { VsolvEntity } from '@vsolv/dev-kit/nest';
import { PlatformConfig } from '@wsphere/platform-config/domain';
import { BaseEntity, Column, PrimaryColumn } from 'typeorm';

@VsolvEntity({ name: 'config', prefix: 'conf' }, 'platform')
export class ConfigEntity extends BaseEntity implements PlatformConfig {
  @PrimaryColumn()
  tenantId!: string;

  @Column()
  productName!: string;

  @Column()
  brandName!: string;

  @Column()
  tagLine!: string;

  @Column()
  prefix!: string;

  @Column()
  prColor!: string;

  @Column({
    nullable: true,
  })
  acColor!: string;

  @Column()
  logo!: string;

  @Column()
  avatar!: string;
}
