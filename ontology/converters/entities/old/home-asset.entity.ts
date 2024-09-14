import { EventPublisher } from '@nestjs/cqrs';
import { AddressEmbeddedEntity } from '@vsolv/core/address/api';
import { mergeObjectContext, VsolvChildEntity } from '@vsolv/dev-kit/nest';
import { AssetEntity } from '@wsphere/assets/api';
import { HomeAsset } from '@wsphere/homes/domain';
import { Column } from 'typeorm';
import { HomeAssetAggregate } from '../models';

@VsolvChildEntity(HomeAsset.Type, 'tenant')
export class HomeAssetEntity extends AssetEntity<typeof HomeAsset.Type> implements HomeAsset.Model {
  @Column()
  size!: number;

  @Column(() => AddressEmbeddedEntity)
  address!: AddressEmbeddedEntity;

  toAggregate(publisher?: EventPublisher): HomeAssetAggregate {
    return mergeObjectContext(
      new HomeAssetAggregate({
        id: this.id,
        referenceId: this.referenceId,

        type: this.type,

        name: this.name,
        description: this.description,

        size: this.size,
        address: this.address.toAggregate(publisher),
      }),
      publisher
    );
  }
}
